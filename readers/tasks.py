from celery import shared_task
from .models import Reader, TagEvent
from datetime import datetime
import base64

@shared_task(queue='webhook_queue')
def process_webhook_data(data):
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
                    TagEvent.objects.create(
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