from celery import shared_task
from .models import Reader, TagEvent, TagTraceability, ReadPoint, MqttTemplate, MQTTTemplateApplicationResult, WebhookTemplate, WebhookTemplateApplicationResult
from datetime import datetime
from django.utils import timezone
import base64
import requests

#@shared_task(queue='webhook_queue')
@shared_task(name='process_webhook')
def process_webhook(data):
    for event in data:
        if event.get('eventType') == 'tagInventory':
            tag_inventory = event.get('tagInventoryEvent')
            if tag_inventory:
                # Determine the reader based on hostname if provided
                reader = None
                hostname = event.get('hostname')
                if hostname:
                    try:
                        reader = Reader.objects.get(name=hostname)
                    except Reader.DoesNotExist:
                        # Create or use a default reader if not found
                        reader, created = Reader.objects.get_or_create(serial_number='default-serial-number', defaults={'name': 'Default Reader'})

                # Handle EPC, checking for either Base64 or Hex format
                epc_hex = None
                epc_base64 = tag_inventory.get('epc')
                if epc_base64:
                    epc_hex = base64.b64decode(epc_base64).hex().upper()
                else:
                    epc_hex = tag_inventory.get('epcHex')

                if epc_hex:
                    timestamp = event.get('timestamp')

                    # Parse optional fields
                    antenna_port = tag_inventory.get('antennaPort')
                    antenna_name = tag_inventory.get('antennaName')
                    peak_rssi_cdbm = tag_inventory.get('peakRssiCdbm')
                    frequency = tag_inventory.get('frequency')
                    transmit_power_cdbm = tag_inventory.get('transmitPowerCdbm')
                    last_seen_time_str = tag_inventory.get('lastSeenTime')
                    tid_base64 = tag_inventory.get('tid')
                    tid_hex = tag_inventory.get('tidHex')

                    # Convert last seen time to datetime object if present
                    last_seen_time = None
                    if last_seen_time_str:
                        try:
                            last_seen_time = datetime.fromisoformat(last_seen_time_str.replace('Z', '+00:00'))
                        except ValueError:
                            last_seen_time = None

                    # Decode tid from base64 if provided
                    if tid_base64 and not tid_hex:
                        tid_hex = base64.b64decode(tid_base64).hex().upper()

                    # Store the data in the database
                    tag_event = TagEvent.objects.create(
                        reader=reader,
                        epc=epc_hex,  # Store the hexadecimal EPC
                        timestamp=timestamp,
                        antenna_port=antenna_port if antenna_port is not None and antenna_port > 0 else None,
                        antenna_name=antenna_name,
                        peak_rssi_cdbm=peak_rssi_cdbm if peak_rssi_cdbm is not None and peak_rssi_cdbm < 0 else None,
                        frequency=frequency if frequency is not None and frequency > 0 else None,
                        transmit_power_cdbm=transmit_power_cdbm if transmit_power_cdbm is not None and transmit_power_cdbm > 0 else None,
                        last_seen_time=last_seen_time,
                        tid=tid_base64,
                        tid_hex=tid_hex
                    )

                    try:
                        from .tasks import process_tag_event
                        process_tag_event.delay(tag_event.id)
                    except:
                        pass


#@shared_task(bind=True, queue='webhook_settings_queue')
@shared_task(name='process_webhook_settings')
def process_webhook_settings(template_id, reader_id):
    try:
        template = WebhookTemplate.objects.get(id=template_id)
        reader = Reader.objects.get(id=reader_id)
        url = f"https://{reader.ip_address}:{reader.port}/api/v1/webhooks/event"
        auth = (reader.username, reader.password)
        response = requests.put(url, json=template.content, auth=auth, headers={'Content-Type': 'application/json'}, verify=False)
        response.raise_for_status()

        # Save success result
        WebhookTemplateApplicationResult.objects.create(
            template=template,
            reader=reader,
            success=True,
            response_message=response.text
        )
    except Exception as e:
        # Save failure result
        WebhookTemplateApplicationResult.objects.create(
            template=template,
            reader=reader,
            success=False,
            response_message=str(e)
        )
        # Retry if the retry flag is true
        raise self.retry(exc=e, countdown=60)

#@shared_task(bind=True, queue='mqtt_settings_queue')
@shared_task(name='process_mqtt_settings')
def process_mqtt_settings(template_id, reader_id):
    try:
        template = MqttTemplate.objects.get(id=template_id)
        reader = Reader.objects.get(id=reader_id)
        url = f"https://{reader.ip_address}:{reader.port}/api/v1/mqtt"
        auth = (reader.username, reader.password)
        response = requests.put(url, json=template.content, auth=auth, headers={'Content-Type': 'application/json'}, verify=False)
        response.raise_for_status()

        # Save success result
        MQTTTemplateApplicationResult.objects.create(
            template=template,
            reader=reader,
            success=True,
            response_message=response.text
        )
    except Exception as e:
        # Save failure result
        MQTTTemplateApplicationResult.objects.create(
            template=template,
            reader=reader,
            success=False,
            response_message=str(e)
        )
        # Retry if the retry flag is true
        raise self.retry(exc=e, countdown=60)
    
@shared_task
def process_departure_time():
    now = timezone.now()
    traceabilities = TagTraceability.objects.filter(departed_at__isnull=True)
    
    for traceability in traceabilities:
        timeout = timedelta(seconds=traceability.read_point.timeout_seconds)
        if now - traceability.arrived_at > timeout:
            traceability.update_departure()

@shared_task
def process_tag_event(tag_event_id):
    try:
        tag_event = TagEvent.objects.get(id=tag_event_id)
        read_point = tag_event.reader.read_point  # Assuming a Reader is associated with a ReadPoint
        timeout = read_point.timeout  # Get the timeout value from the ReadPoint

        # Check if there's an existing traceability record for this EPC at this read point
        traceability, created = TagTraceability.objects.get_or_create(
            epc=tag_event.epc, 
            read_point=read_point,
            defaults={
                'arrived_at': tag_event.timestamp, 
                'last_seen': tag_event.timestamp, 
                'departed_at': None
            }
        )

        if not created:
            # If the tag was seen before the timeout expired, update the last seen time
            if traceability.departed_at is None and (tag_event.timestamp - traceability.last_seen).total_seconds() <= timeout:
                traceability.last_seen = tag_event.timestamp
                traceability.save()
            else:
                # If the timeout expired, update the departure time and create a new arrival event
                if traceability.departed_at is None:
                    traceability.departed_at = traceability.last_seen + timezone.timedelta(seconds=timeout)
                    traceability.save()

                # Now treat this event as a new arrival
                traceability.arrived_at = tag_event.timestamp
                traceability.last_seen = tag_event.timestamp
                traceability.departed_at = None
                traceability.save()

        # Optionally, you might want to handle cases where there is no subsequent event, 
        # and a background task might update the departure time after the timeout.

    except TagEvent.DoesNotExist:
        pass  # Handle the case where the TagEvent doesn't exist