# smartreader/mqtt_subscriber.py

import paho.mqtt.client as mqtt
import json
import logging
from django.conf import settings
from django.utils import timezone
from apps.readers.models import Reader, TagEvent, SmartReader
from apps.smartreader.models import MQTTConfiguration, MQTTCommand, StatusEvent, ConnectionEvent, DisconnectionEvent, InventoryStatusEvent, HeartbeatEvent, GPIEvent
from .utils import parse_status_event
from .utils import execute_alerts_for_event
from .utils import process_tag_event_data

# Set up logging
logger = logging.getLogger(__name__)

def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode('utf-8'))

        # Extract the SmartReader serial number from the topic
        topic_parts = msg.topic.split('/')
        if len(topic_parts) >= 2 and topic_parts[0] == 'smartreader':
            serial_number = topic_parts[1]

            # Retrieve the corresponding SmartReader object
            smartreader = SmartReader.objects.filter(reader_serial=serial_number).first()

            if smartreader:
                # Retrieve the MQTTConfiguration for the smartreader
                config = MQTTConfiguration.objects.filter(smartreader=smartreader).first()

                if not config:
                    logger.warning(f"No MQTT configuration found for SmartReader with serial number {serial_number}.")
                    return

                # Extract the last part of each topic for comparison
                tag_events_topic_end = config.tag_events_topic.split('/')[-1]
                management_command_response_topic_end = config.management_command_response_topic.split('/')[-1]
                control_command_response_topic_end = config.control_command_response_topic.split('/')[-1]
                management_events_topic_end = config.management_events_topic.split('/')[-1]

                # Extract the last part of the received message topic
                msg_topic_end = topic_parts[-1]

                # Pass the SmartReader object to the appropriate handler based on the configuration topics
                if msg_topic_end == tag_events_topic_end:
                    handle_tag_event(data, smartreader)
                elif msg_topic_end == management_command_response_topic_end:
                    handle_management_command_response(data, smartreader)
                elif msg_topic_end == control_command_response_topic_end:
                    handle_control_command_response(data, smartreader)
                elif msg_topic_end == management_events_topic_end:
                    handle_management_event(data, smartreader)
                else:
                    logger.warning(f"Unhandled topic: {msg.topic}")
            else:
                logger.warning(f"SmartReader with serial number {serial_number} not found.")
    except Exception as e:
        logger.error(f"Failed to process message from topic {msg.topic}: {e}", exc_info=True)

def handle_tag_event(data, smartreader):
    serial_number = data.get('serial_number')
    epc = data.get('epc')
    timestamp = timezone.now()
    antenna_port = data.get('antenna_port')

    # Get the corresponding reader
    reader = Reader.objects.filter(serial_number=serial_number).first()
    if reader:
        # Create and save a TagEvent instance
        process_tag_event_data(data, smartreader)
    else:
        logger.warning(f"Reader with serial number {serial_number} not found.")

def handle_management_command_response(data, smartreader):
    # Example: Handle the response to a management command
    command_id = data.get('command_id')
    status = data.get('status')
    response_payload = data.get('response_payload', {})

    # Update the corresponding MQTTCommand with the status and response
    MQTTCommand.objects.filter(command_id=command_id).update(
        status=status,
        response=response_payload,
        updated_at=timezone.now()
    )

def handle_control_command_response(data, smartreader):
    # Example: Handle the response to a control command
    command_id = data.get('command_id')
    status = data.get('status')
    response_payload = data.get('response_payload', {})

    # Update the corresponding MQTTCommand with the status and response
    MQTTCommand.objects.filter(command_id=command_id).update(
        status=status,
        response=response_payload,
        updated_at=timezone.now()
    )

def handle_management_event(data, smartreader):
    event_type = data.get('eventType')
    if event_type == 'status':
        handle_status_event(data, smartreader)
    elif 'smartreader-mqtt-status' in data:
        handle_connection_event(data, smartreader)
    elif data.get('status') == 'running':
        handle_inventory_status_event(data, smartreader)
    elif 'isHeartBeat' in data.get('tag_reads', [{}])[0]:
        handle_heartbeat_event(data, smartreader)
    elif event_type == 'gpi-status':
        handle_gpi_event(data, smartreader)
    else:
        logger.warning(f"Unhandled management event: {data}")

def handle_status_event(data, smartreader):
    # Extract and save status event data
    parse_status_event(data, smartreader)

def handle_connection_event(data, smartreader):
    # Handle connection event
    received_event = ConnectionEvent.objects.create(
        smartreader=smartreader,
        status=data.get('smartreader-mqtt-status')
    )
    execute_alerts_for_event(received_event)

def handle_disconnection_event(data, smartreader):
    # Handle disconnection event
    received_event = DisconnectionEvent.objects.create(
        smartreader=smartreader,
        status=data.get('smartreader-mqtt-status')
    )
    execute_alerts_for_event(received_event)

def handle_inventory_status_event(data, smartreader):
    # Handle inventory status event
    received_event = InventoryStatusEvent.objects.create(
        smartreader=smartreader,
        status=data.get('status')
    )
    execute_alerts_for_event(received_event)

def handle_heartbeat_event(data, smartreader):
    # Handle heartbeat event
    received_event = HeartbeatEvent.objects.create(
        smartreader=smartreader,
        reader_name=data.get('readerName'),
        mac_address=data.get('mac'),
        tag_reads=data.get('tag_reads')
    )
    execute_alerts_for_event(received_event)

def handle_gpi_event(data, smartreader):
    gpi_configurations = data.get('gpiConfigurations', [])
    
    # Assuming gpi_configurations will always have two elements for GPI 1 and GPI 2
    gpi1_config = next((gpi for gpi in gpi_configurations if gpi['gpi'] == 1), None)
    gpi2_config = next((gpi for gpi in gpi_configurations if gpi['gpi'] == 2), None)

    gpi1_state = gpi1_config['state'] if gpi1_config else 'unknown'
    gpi2_state = gpi2_config['state'] if gpi2_config else 'unknown'

    # Create and save a GPIEvent instance
    received_event = GPIEvent.objects.create(
        smartreader=smartreader,
        reader_name=data.get('readerName'),
        mac_address=data.get('mac'),
        timestamp=timezone.datetime.fromtimestamp(data.get('timestamp') / 1e6),
        gpi1_state=gpi1_state,
        gpi2_state=gpi2_state
    )
    execute_alerts_for_event(received_event)

def start_mqtt_subscriber():
    configurations = MQTTConfiguration.objects.all()
    for config in configurations:
        client = mqtt.Client()

        # Connect to the broker
        client.connect(config.broker_hostname, config.broker_port, 60)

        # Set the on_message callback
        client.on_message = on_message

        # Subscribe to the relevant topics
        client.subscribe(config.tag_events_topic, qos=config.tag_events_qos)
        client.subscribe(config.management_command_response_topic, qos=config.management_command_qos)
        client.subscribe(config.control_command_response_topic, qos=config.control_command_qos)
        client.subscribe(config.management_events_topic, qos=config.management_command_qos)

        # Start the MQTT loop
        client.loop_start()

if __name__ == "__main__":
    start_mqtt_subscriber()
