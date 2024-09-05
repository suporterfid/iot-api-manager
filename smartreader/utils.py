import json
from django.utils.dateparse import parse_datetime
from readers.models import Reader, TagEvent
from .models import Smartreader, StatusEvent, ConnectionEvent, DisconnectionEvent, InventoryStatusEvent, GPIEvent, AntennaStatus, HeartbeatEvent, Alert
from datetime import datetime
from django.utils import timezone
import base64

def get_event_model_fields():
    event_models = {
        'StatusEvent': StatusEvent,
        'ConnectionEvent': ConnectionEvent,
        'DisconnectionEvent': DisconnectionEvent,
        'InventoryStatusEvent': InventoryStatusEvent,
        'GPIEvent': GPIEvent,
        'AntennaStatus': AntennaStatus,
        'HeartbeatEvent': HeartbeatEvent,
    }

    event_fields = {}
    for event_name, event_model in event_models.items():
        fields = [f.name for f in event_model._meta.get_fields()]
        event_fields[event_name] = fields

    return event_fields

def process_tag_event_data(event, smartreader):
    if event.get('eventType') == 'tagInventory':
        tag_inventory = event.get('tagInventoryEvent')
        if tag_inventory:
            # Determine the reader based on hostname if provided
            reader = None
            hostname = event.get('hostname')
            if hostname:
                try:
                    reader = Reader.objects.get(serial_number=smartreader.reader_serial)
                except Reader.DoesNotExist:
                    # Create or use a default reader if not found
                    reader, created = Reader.objects.get_or_create(serial_number='default-serial-number', defaults={'name': hostname})

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
                except Exception as e:
                    # Optionally log this exception
                    pass
    # Handle the second type of tag event
    elif 'tag_reads' in event:
        reader_name = event.get('readerName')
        mac_address = event.get('mac')
        tag_reads = event.get('tag_reads')

        # Find or create the reader by its name
        reader = None
        if reader_name:
            try:
                reader = Reader.objects.get(name=reader_name)
            except Reader.DoesNotExist:
                # Create or use a default reader if not found
                reader, created = Reader.objects.get_or_create(serial_number='default-serial-number', defaults={'name': reader_name})

        for tag_read in tag_reads:
            epc = tag_read.get('epc')
            first_seen_timestamp = tag_read.get('firstSeenTimestamp')
            antenna_port = tag_read.get('antennaPort')
            antenna_name = tag_read.get('antennaZone')
            peak_rssi = tag_read.get('peakRssi')
            tx_power = tag_read.get('txPower')
            tid = tag_read.get('tid')
            rf_phase = tag_read.get('rfPhase')
            frequency = tag_read.get('frequency')
            tag_data_key = tag_read.get('tagDataKey')
            tag_data_key_name = tag_read.get('tagDataKeyName')
            tag_data_serial = tag_read.get('tagDataSerial')

            # Convert the timestamp to a datetime object
            timestamp = None
            if first_seen_timestamp:
                timestamp = datetime.fromtimestamp(first_seen_timestamp / 1e6)

            # Store the data in the database
            tag_event = TagEvent.objects.create(
                reader=reader,
                epc=epc,
                timestamp=timestamp,
                antenna_port=antenna_port,
                antenna_name=antenna_name,
                peak_rssi_cdbm=peak_rssi,
                transmit_power_cdbm=tx_power,
                tid=tid,
                rf_phase=rf_phase,
                frequency=frequency,
                tag_data_key=tag_data_key,
                tag_data_key_name=tag_data_key_name,
                tag_data_serial=tag_data_serial
            )

            try:
                from .tasks import process_tag_event
                process_tag_event.delay(tag_event.id)
            except Exception as e:
                # Optionally log this exception
                pass

def parse_status_event(json_data, smartreader):
    # Step 1: Parse general status event data
    status_event = StatusEvent(
        smartreader=smartreader,
        reader_name=json_data.get('readerName'),
        timestamp=parse_datetime(json_data.get('timestamp')),
        mac_address=json_data.get('macAddress'),
        status=json_data.get('status'),
        component=json_data.get('component'),
        ip_addresses=json_data.get('ipAddresses'),
        active_preset=json_data.get('activePreset'),
        manufacturer=json_data.get('manufacturer'),
        product_hla=json_data.get('productHla'),
        product_model=json_data.get('productModel'),
        product_sku=json_data.get('productSku'),
        product_description=json_data.get('productDescription'),
        is_antenna_hub_enabled=json_data.get('isAntennaHubEnabled') == 'True',
        reader_operating_region=json_data.get('readerOperatingRegion'),
        gpi1=json_data.get('gpi1'),
        gpi2=json_data.get('gpi2'),
        gpo1_admin_status=json_data.get('GPO1AdminStatus'),
        gpo2_admin_status=json_data.get('GPO2AdminStatus'),
        gpo3_admin_status=json_data.get('GPO3AdminStatus'),
        gpo1_operation_status=json_data.get('GPO1OperationStatus'),
        gpo2_operation_status=json_data.get('GPO2OperationStatus'),
        gpo3_operation_status=json_data.get('GPO3OperationStatus'),
        boot_env_version=json_data.get('BootEnvVersion'),
        hla_version=json_data.get('HLAVersion'),
        hardware_version=json_data.get('HardwareVersion'),
        int_hardware_version=json_data.get('IntHardwareVersion'),
        model_name=json_data.get('ModelName'),
        serial_number=json_data.get('SerialNumber'),
        int_serial_number=json_data.get('IntSerialNumber'),
        features_valid=json_data.get('FeaturesValid'),
        bios_version=json_data.get('BIOSVersion'),
        ptn=json_data.get('PTN'),
        uptime_seconds=int(json_data.get('UptimeSeconds', 0)),
        boot_status=json_data.get('BootStatus'),
        boot_reason=json_data.get('BootReason'),
        power_fail_time=int(json_data.get('PowerFailTime', 0)),
        active_power_source=json_data.get('ActivePowerSource'),
        total_memory=int(json_data.get('TotalMemory', 0)),
        free_memory=int(json_data.get('FreeMemory', 0)),
        used_memory=int(json_data.get('UsedMemory', 0)),
        cpu_utilization=int(json_data.get('CPUUtilization', 0)),
        total_configuration_storage_space=int(json_data.get('TotalConfigurationStorageSpace', 0)),
        free_configuration_storage_space=int(json_data.get('FreeConfigurationStorageSpace', 0)),
        total_application_storage_space=int(json_data.get('TotalApplicationStorageSpace', 0)),
        free_application_storage_space=int(json_data.get('FreeApplicationStorageSpace', 0)),
        service_enabled=json_data.get('ServiceEnabled') == 'True',
        negotiation_timeout=int(json_data.get('NegotiationTimeout', 0)),
        poe_plus_required=json_data.get('PoePlusRequired') == 'True',
        negotiation_state=json_data.get('NegotiationState'),
        required_power_available=json_data.get('RequiredPowerAvailable'),
        requested_power=int(json_data.get('RequestedPower', 0)),
        allocated_power=int(json_data.get('AllocatedPower', 0)),
        power_source=json_data.get('PowerSource'),
        primary_image_type=json_data.get('PrimaryImageType'),
        primary_image_state=json_data.get('PrimaryImageState'),
        primary_image_system_version=json_data.get('PrimaryImageSystemVersion'),
        primary_image_config_version=json_data.get('PrimaryImageConfigVersion'),
        primary_image_custom_app_version=json_data.get('PrimaryImageCustomAppVersion'),
        secondary_image_type=json_data.get('SecondaryImageType'),
        secondary_image_state=json_data.get('SecondaryImageState'),
        secondary_image_system_version=json_data.get('SecondaryImageSystemVersion'),
        secondary_image_config_version=json_data.get('SecondaryImageConfigVersion'),
        secondary_image_custom_app_version=json_data.get('SecondaryImageCustomAppVersion'),
    )
    
    # Save the StatusEvent instance
    status_event.save()

    # Step 2: Parse and save antenna data
    for i in range(1, 33):  # Assuming antenna numbers range from 1 to 32
        antenna_key = f'antenna{i}'
        if f'{antenna_key}Enabled' in json_data:
            antenna_status = AntennaStatus(
                status_event=status_event,
                antenna_number=i,
                enabled=json_data.get(f'{antenna_key}Enabled') == 'True',
                zone=json_data.get(f'{antenna_key}Zone'),
                tx_power=int(json_data.get(f'{antenna_key}TxPower', 0)),
                rx_sensitivity=int(json_data.get(f'{antenna_key}RxSensitivity', 0)),
                operational_status=json_data.get(f'{antenna_key}OperationalStatus'),
                last_power_level=int(json_data.get(f'{antenna_key}LastPowerLevel', 0)),
                last_noise_level=int(json_data.get(f'{antenna_key}LastNoiseLevel', 0)),
                energized_time=int(json_data.get(f'{antenna_key}EnergizedTime', 0)),
                unique_inventory_count=int(json_data.get(f'{antenna_key}UniqueInventoryCount', 0)),
                total_inventory_count=int(json_data.get(f'{antenna_key}TotalInventoryCount', 0)),
                failed_inventory_count=int(json_data.get(f'{antenna_key}FailedInventoryCount', 0)),
                read_count=int(json_data.get(f'{antenna_key}ReadCount', 0)),
                failed_read_count=int(json_data.get(f'{antenna_key}FailedReadCount', 0)),
                write_count=int(json_data.get(f'{antenna_key}WriteCount', 0)),
                failed_write_count=int(json_data.get(f'{antenna_key}FailedWriteCount', 0)),
                lock_count=int(json_data.get(f'{antenna_key}LockCount', 0)),
                failed_lock_count=int(json_data.get(f'{antenna_key}FailedLockCount', 0)),
                kill_count=int(json_data.get(f'{antenna_key}KillCount', 0)),
                failed_kill_count=int(json_data.get(f'{antenna_key}FailedKillCount', 0)),
                erase_count=int(json_data.get(f'{antenna_key}EraseCount', 0)),
                failed_erase_count=int(json_data.get(f'{antenna_key}FailedEraseCount', 0)),
            )
            
            # Save the AntennaStatus instance
            antenna_status.save()

    # Step 3: Execute alerts for this event
    execute_alerts_for_event(status_event)

def execute_alerts_for_event(event):
    """
    Execute all alerts related to a given event type.
    """
    event_class_name = event.__class__.__name__
    
    # Get all alerts that are relevant to the event type
    alerts = Alert.objects.filter(conditions__field__icontains=event_class_name).distinct()
    
    for alert in alerts:
        if alert.check_conditions(event):
            alert.trigger(event)
