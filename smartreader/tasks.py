# smartreader/tasks.py
from celery import shared_task
from .models import SmartReader, MQTTCommand, MqttCommandTemplate, StatusEvent, AlertRule, Alert
from readers.models import TagEvent
import paho.mqtt as mqtt
import paho.mqtt.publish as publish
from django.conf import settings
import json
import requests
import logging

# Set up logging
logger = logging.getLogger(__name__)

@shared_task
def process_event_for_alerts(event_id, event_type):
    """Process any event and evaluate it against all applicable alert rules."""
    event_model = {
        'StatusEvent': StatusEvent,
        'TagEvent': TagEvent,
        # Add other event models as necessary
    }.get(event_type, None)

    if not event_model:
        logger.error(f"Event type {event_type} is not recognized.")
        return

    try:
        event = event_model.objects.get(id=event_id)
    except event_model.DoesNotExist:
        logger.error(f"Event with ID {event_id} does not exist for type {event_type}.")
        return

    rules = AlertRule.objects.filter(smartreaders__in=[event.smartreader], active=True)

    for rule in rules:
        conditions_met = True
        previous_event = event_model.objects.filter(smartreader=event.smartreader).order_by('-timestamp').exclude(id=event_id).first()
        
        for condition in rule.conditions.all():
            field_value = getattr(event, condition.field_name, None)
            previous_value = getattr(previous_event, condition.field_name, None) if previous_event else None

            if field_value is None:
                logger.warning(f"Field {condition.field_name} is None in the event data.")
                conditions_met = False
                break

            if not evaluate_condition(field_value, condition.operator, condition.threshold, previous_value):
                conditions_met = False
                break
        
        if conditions_met:
            try:
                Alert.objects.create(alert_rule=rule, event_data=event)
                execute_alert_actions(rule, event)
            except Exception as e:
                logger.error(f"Failed to create alert or execute actions for rule {rule.name}: {e}", exc_info=True)

def evaluate_condition(field_value, operator, threshold, previous_value=None):
    """Evaluate a single condition against the current and optionally previous field value."""
    try:
        if operator == '>':
            return field_value > float(threshold)
        elif operator == '<':
            return field_value < float(threshold)
        elif operator == '=':
            return str(field_value) == str(threshold)
        elif operator == 'remains the same' and previous_value is not None:
            return field_value == previous_value
        elif operator == 'greater than previous' and previous_value is not None:
            return field_value > previous_value
        elif operator == 'less than previous' and previous_value is not None:
            return field_value < previous_value
    except (TypeError, ValueError) as e:
        logger.error(f"Error evaluating condition: {e}", exc_info=True)
    return False

def execute_alert_actions(rule, event):
    """Execute the actions associated with the rule when the conditions are met."""
    for action in rule.actions.all():
        try:
            if action.action_type == 'webhook':
                trigger_webhook(action.action_value, rule.name, event)
            elif action.action_type == 'mqtt':
                send_mqtt_message(action.action_value, json.dumps(event.get_event_data()), action.parameters)
        except Exception as e:
            logger.error(f"Failed to execute action {action.action_type} for rule {rule.name}: {e}", exc_info=True)

@shared_task
def send_mqtt_message(topic, message, parameters=None):
    """Send an MQTT message to a specific topic with optional parameters."""
    try:
        client = mqtt.Client()

        # Extract MQTT connection parameters from the parameters field
        broker_url = parameters.get('broker_url', 'localhost') if parameters else 'localhost'
        broker_port = int(parameters.get('broker_port', 1883)) if parameters else 1883
        keepalive_interval = int(parameters.get('keepalive_interval', 60)) if parameters else 60
        username = parameters.get('username') if parameters else None
        password = parameters.get('password') if parameters else None
        use_tls = parameters.get('use_tls', False) if parameters else False
        tls_ca_certs = parameters.get('tls_ca_certs') if parameters else None

        # Apply optional parameters like QoS, retain, etc.
        qos = int(parameters.get('qos', 1)) if parameters else 1
        retain = bool(parameters.get('retain', False)) if parameters else False

        if username and password:
            client.username_pw_set(username, password)

        if use_tls and tls_ca_certs:
            client.tls_set(tls_ca_certs)

        client.connect(broker_url, broker_port, keepalive_interval)
        client.loop_start()

        client.publish(topic, message, qos=qos, retain=retain)
        client.loop_stop()

        client.disconnect()
    except Exception as e:
        logger.error(f"Failed to send MQTT message: {e}", exc_info=True)

def trigger_webhook(url, rule_name, event, message, parameters=None):
    """Trigger a webhook action with optional parameters."""
    try:
        headers = {'Content-Type': 'application/json'}
        if parameters and 'headers' in parameters:
            headers.update(parameters['headers'])

        timeout = int(parameters.get('timeout', 10)) if parameters else 10

        response = requests.post(url, data=message, headers=headers, timeout=timeout)
        response.raise_for_status()
        logger.info(f"Webhook for rule '{rule_name}' triggered successfully.")
    except requests.RequestException as e:
        logger.error(f"Failed to trigger webhook for rule '{rule_name}': {e}", exc_info=True)

@shared_task
def send_mqtt_command(mqtt_command_id):
    """Send an MQTT command to all selected SmartReaders."""
    mqtt_command = MQTTCommand.objects.get(id=mqtt_command_id)
    smartreaders = mqtt_command.smartreaders.all()
    command_template = mqtt_command.command_template
    command_json = json.loads(command_template.template_content)

    for smartreader in smartreaders:
        try:
            # Customize the command JSON with dynamic data from SmartReader
            command_json["command_id"] = f"{command_template.name}-{smartreader.reader_serial}"
            command_json["payload"]["reader_serial"] = smartreader.reader_serial
            command_json["payload"]["timestamp"] = str(mqtt_command.created_at)
            
            # Determine the correct topic based on the command type
            if command_template.command_type == MqttCommandTemplate.COMMAND_TYPE_CONTROL:
                topic = f"{smartreader.mqtt_control_command_topic}"
            elif command_template.command_type == MqttCommandTemplate.COMMAND_TYPE_MANAGEMENT:
                topic = f"{smartreader.mqtt_management_command_topic}"
            else:
                logger.warning(f"Unknown command type for template {command_template.name}")
                continue
            
            # Convert the command JSON to string for MQTT payload
            payload = json.dumps(command_json)

            # Send the MQTT command
            publish.single(
                topic,
                payload=payload,
                hostname=smartreader.mqtt_broker_address,
                port=smartreader.mqtt_broker_port,
                qos=1,
                retain=False,
                auth={
                    'username': smartreader.mqtt_username,
                    'password': smartreader.mqtt_password,
                } if smartreader.mqtt_username and smartreader.mqtt_password else None
            )

            # Update the command status to success
            mqtt_command.status = MQTTCommand.STATE_SUCCESS
            mqtt_command.response = {
                'message': 'Command sent successfully',
                'smartreader_id': smartreader.id
            }
            mqtt_command.save()

        except Exception as e:
            # Handle any errors during the sending process
            mqtt_command.status = MQTTCommand.STATE_ERROR
            mqtt_command.response = {
                'error': str(e),
                'smartreader_id': smartreader.id
            }
            mqtt_command.save()
            logger.error(f"Failed to send MQTT command to {smartreader.reader_serial}: {e}", exc_info=True)
