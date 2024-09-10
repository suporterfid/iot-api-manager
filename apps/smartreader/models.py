from django.db import models
from django.utils import timezone
from apps.readers.models import Reader
from .json_utils import json_field  # Importando o decorator do utils.py
from django.contrib.auth.models import User
import uuid
import json
import logging
from django.core.exceptions import FieldDoesNotExist

logger = logging.getLogger(__name__)

class AlertRule(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    smartreaders = models.ManyToManyField('SmartReader', related_name='alert_rules')
    active = models.BooleanField(default=True)
    last_triggered = models.DateTimeField(null=True, blank=True)
    trigger_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clone(self):
        # Create a copy of the AlertRule object
        cloned_rule = AlertRule.objects.create(
            name=f"{self.name} (Clone)",
            description=self.description,
            created_by=self.created_by,
            active=self.active,
            last_triggered=None,  # Reset to None for the cloned rule
            trigger_count=0,  # Reset the trigger count
        )

        # Copy smartreaders to the cloned rule
        cloned_rule.smartreaders.set(self.smartreaders.all())

        # Clone conditions and actions
        for condition in self.conditions.all():
            condition.pk = None  # Reset the primary key to create a new instance
            condition.alert_rule = cloned_rule
            condition.save()

        for action in self.actions.all():
            action.pk = None  # Reset the primary key to create a new instance
            action.alert_rule = cloned_rule
            action.save()

        return cloned_rule

    def __str__(self):
        return self.name

class AlertCondition(models.Model):
    CONDITION_TYPES = [
        ('StatusEvent', 'Status Event'),
        ('ConnectionEvent', 'Connection Event'),
        ('DisconnectionEvent', 'Disconnection Event'),
        ('InventoryStatusEvent', 'Inventory Status Event'),
        ('GPIEvent', 'GPI Event'),
        ('AntennaStatus', 'Antenna Status'),
        ('HeartbeatEvent', 'Heartbeat Event'),
        ('CustomEvent', 'Custom Event'),
    ]

    OPERATORS = [
            ('>', 'Greater than'),
            ('<', 'Less than'),
            ('=', 'Equal to'),
    ]

    COMPARISON_TYPES = [
        ('equals', 'Equals'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('remains_same', 'Remains the Same'),
    ]
        
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='conditions')
    event_type = models.CharField(max_length=255) 
    field_name = models.CharField(max_length=255)  # e.g., 'cpu_utilization'
    operator = models.CharField(max_length=10)  # e.g., '>', '<', '='
    comparison_type = models.CharField(max_length=50, choices=COMPARISON_TYPES)
    threshold = models.CharField(max_length=255)  # e.g., '80'
    recurrence = models.IntegerField(null=True, blank=True)  # number of occurrences before alert is triggered

    def __str__(self):
        return f'{self.field_name} {self.operator} {self.threshold}'

class AlertAction(models.Model):
    ACTION_TYPE_CHOICES = [
        ('mqtt', 'MQTT'),
        ('webhook', 'Webhook'),
    ]
    
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='actions')
    action_type = models.CharField(max_length=50, choices=ACTION_TYPE_CHOICES)
    action_value = models.CharField(max_length=255)
    parameters = models.CharField(max_length=1024, null=True, blank=True)  # Parameters in key=value; format
    message_template = models.TextField(null=True, blank=True)  # Template for custom messages
    order = models.IntegerField(default=0)  # Order of execution

    def __str__(self):
        return f'{self.action_type} - {self.action_value}'
    
    def execute(self, event):
        """Execute the action, populating the message and parameters if necessary."""
        if self.action_type == 'mqtt':
            topic = self.action_value
            message = self._populate_message(event)
            from .tasks import send_mqtt_message
            send_mqtt_message(topic, message)
        elif self.action_type == 'webhook':
            url = self.action_value
            payload = self._populate_message(event)
            from .tasks import trigger_webhook
            trigger_webhook(url, payload)
            
    def _parse_parameters(self):
        if self.parameters:
            return dict(param.split('=') for param in self.parameters.split(';') if '=' in param)
        return {}

    def _populate_message(self, event):
        """Populate the message template with event data."""
        if self.message_template:
            return self.message_template.format(
                reader_name=event.reader_name,
                event_type=event.__class__.__name__,
                timestamp=event.timestamp,
                **event.get_event_data()
            )
        return json.dumps(event.get_event_data())

class Alert(models.Model):
    alert_rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='alerts')
    triggered_at = models.DateTimeField(auto_now_add=True)
    event_data = models.JSONField()  # Store the event data that triggered the alert
    resolved = models.BooleanField(default=False)
    conditions = models.ManyToManyField('Condition')  # Use a string reference here

    def check_conditions(self, event):
        previous_event = self.get_previous_event(event)
        for condition in self.conditions.all():
            if not condition.evaluate(event, previous_event):
                return False
        return True

    def get_previous_event(self, current_event):
        # Fetch the previous event of the same type for the same SmartReader
        event_type = type(current_event)
        return event_type.objects.filter(
            smartreader=current_event.smartreader,
            timestamp__lt=current_event.timestamp
        ).order_by('-timestamp').first()

    def __str__(self):
        return f'Alert for {self.alert_rule.name} at {self.triggered_at}'
    
class Condition(models.Model):
    # Existing fields
    field = models.CharField(max_length=255)
    value = models.CharField(max_length=255)
    
    # New fields for comparison with the previous event
    comparison_type = models.CharField(
        max_length=50,
        choices=[
            ('remains_same', 'Remains the Same'),
            ('greater_than', 'Greater Than'),
            ('lower_than', 'Lower Than'),
        ],
        null=True,
        blank=True
    )
    compare_with_previous = models.BooleanField(default=False)

    def evaluate(self, event, previous_event=None):
        current_value = getattr(event, self.field)
        if self.compare_with_previous and previous_event:
            previous_value = getattr(previous_event, self.field)
            if self.comparison_type == 'remains_same':
                return current_value == previous_value
            elif self.comparison_type == 'greater_than':
                return current_value > previous_value
            elif self.comparison_type == 'lower_than':
                return current_value < previous_value
        else:
            return current_value == self.value

class SmartReader(models.Model):
    # Define status choices
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('maintenance', 'Maintenance'),
    ]

    # field using STATUS_CHOICES
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='inactive')

    # Basic Reader Information
    active_plugin = models.CharField(max_length=255, null=True, blank=True)
    advanced_gpo_enabled = models.BooleanField(default=False)
    advanced_gpo_mode_1  = models.IntegerField(null=True, blank=True, default=0)
    advanced_gpo_mode_2  = models.IntegerField(null=True, blank=True, default=0)
    advanced_gpo_mode_3  = models.IntegerField(null=True, blank=True, default=0)
    advanced_gpo_mode_4  = models.IntegerField(null=True, blank=True, default=0)
    antenna_identifier = models.CharField(max_length=255, null=True, blank=True)
    antenna_ports = models.CharField(max_length=255, default='1,2,3,4')
    antenna_states = models.CharField(max_length=255, default='1,0,0,0')
    antenna_zones = models.CharField(max_length=255, default='antenna,antenna,antenna,antenna')
    apply_ip_settings_on_startup = models.BooleanField(default=False)
    backup_to_flash_drive_on_gpi_event_enabled = models.BooleanField(default=False)
    backup_to_internal_flash_enabled = models.BooleanField(default=False)
    barcode_enable_queue = models.BooleanField(default=False)
    barcode_line_end = models.IntegerField(null=True, blank=True)
    barcode_no_data_string = models.CharField(max_length=255, null=True, blank=True)
    barcode_process_no_data_string = models.BooleanField(default=False)
    barcode_tcp_address = models.CharField(max_length=255, null=True, blank=True)
    barcode_tcp_len = models.IntegerField(null=True, blank=True)
    barcode_tcp_no_data_string = models.CharField(max_length=255, null=True, blank=True)
    barcode_tcp_port = models.IntegerField(null=True, blank=True)
    baud_rate = models.IntegerField(null=True, blank=True)
    broadcast_address = models.GenericIPAddressField(null=True, blank=True)
    c1g2_filter_enabled = models.BooleanField(default=False) 
    c1g2_filter_bank = models.CharField(max_length=255, null=True, blank=True)
    c1g2_filter_len = models.CharField(max_length=255, null=True, blank=True) 
    c1g2_filter_mask = models.CharField(max_length=255, null=True, blank=True) 
    c1g2_filter_match_option = models.CharField(max_length=255, null=True, blank=True)
    c1g2_filter_pointer = models.CharField(max_length=255, null=True, blank=True) 
    cleanup_tag_events_list_batch_on_reload = models.BooleanField(default=False)
    connection_status= models.BooleanField(default=False)
    csv_file_format = models.IntegerField(default=False)
    custom_field_1_enabled = models.BooleanField(default=False)
    custom_field_1_name = models.CharField(max_length=255, null=True, blank=True)
    custom_field_1_value = models.CharField(max_length=255, null=True, blank=True)
    custom_field_2_enabled = models.BooleanField(default=False)
    custom_field_2_name = models.CharField(max_length=255, null=True, blank=True)
    custom_field_2_value = models.CharField(max_length=255, null=True, blank=True)
    custom_field_3_enabled = models.BooleanField(default=False)
    custom_field_3_name = models.CharField(max_length=255, null=True, blank=True)
    custom_field_3_value = models.CharField(max_length=255, null=True, blank=True)
    custom_field_4_enabled = models.BooleanField(default=False)
    custom_field_4_name = models.CharField(max_length=255, null=True, blank=True)
    custom_field_4_value = models.CharField(max_length=255, null=True, blank=True)
    data_prefix = models.CharField(max_length=255, null=True, blank=True)
    data_suffix = models.CharField(max_length=255, null=True, blank=True)
    empty_field_timeout = models.IntegerField(null=True, blank=True) 
    enable_antenna_task = models.BooleanField(default=False)
    enable_barcode_hid = models.BooleanField(default=False)
    enable_barcode_serial = models.BooleanField(default=False)
    enable_barcode_tcp = models.BooleanField(default=False)
    enable_external_api_verification = models.BooleanField(default=False)
    enable_plugin = models.BooleanField(default=False)
    enable_plugin_shipment_verification = models.BooleanField(default=False)
    enable_partial_validation = models.BooleanField(default=False)
    mqtt_enable_smartreader_default_topics = models.BooleanField(default=False)
    enable_summary_stream = models.BooleanField(default=False)
    enable_tag_event_stream = models.BooleanField(default=False)
    enable_tag_events_list_batch = models.BooleanField(default=False)
    enable_tag_events_list_batch_publishing = models.BooleanField(default=False)
    enable_unique_tag_read = models.BooleanField(default=False)
    enable_validation = models.BooleanField(default=False)
    external_api_verification_auth_login_url = models.URLField(max_length=2048, null=True, blank=True)
    external_api_verification_change_order_status_url = models.URLField(max_length=2048, null=True, blank=True)
    external_api_verification_http_header_name = models.CharField(max_length=255, null=True, blank=True)
    external_api_verification_http_header_value = models.CharField(max_length=255, null=True, blank=True)
    external_api_verification_publish_data_url = models.URLField(max_length=2048, null=True, blank=True)
    external_api_verification_search_order_url = models.URLField(max_length=2048, null=True, blank=True)
    external_api_verification_search_product_url = models.URLField(max_length=2048, null=True, blank=True)
    filter_tag_events_list_batch_on_change_based_on_antenna_zone = models.BooleanField(default=False)
    field_delim = models.CharField(max_length=255, null=True, blank=True)
    field_ping_interval = models.IntegerField(null=True, blank=True) 
    gateway_address = models.GenericIPAddressField(null=True, blank=True)
    group_events_on_inventory_status = models.BooleanField(default=False)
    gtin_output_type = models.IntegerField(null=True, blank=True)
    heartbeat_enabled = models.BooleanField(default=False)
    heartbeat_http_authentication_username = models.CharField(max_length=255, null=True, blank=True)
    heartbeat_http_authentication_password = models.CharField(max_length=255, null=True, blank=True)
    heartbeat_http_authentication_token_api_body = models.TextField(null=True, blank=True)
    heartbeat_http_authentication_token_api_enabled = models.BooleanField(default=False)
    heartbeat_http_authentication_token_api_password_field = models.CharField(max_length=255, null=True, blank=True)
    heartbeat_http_authentication_token_api_password_value = models.CharField(max_length=255, null=True, blank=True)
    heartbeat_http_authentication_token_api_username_field = models.CharField(max_length=255, null=True, blank=True)
    heartbeat_http_authentication_token_api_username_value = models.CharField(max_length=255, null=True, blank=True)
    heartbeat_http_authentication_token_api_url = models.URLField(max_length=2048, null=True, blank=True)
    heartbeat_http_authentication_token_api_value = models.TextField(null=True, blank=True)
    heartbeat_http_authentication_type = models.CharField(max_length=50, null=True, blank=True)
    heartbeat_period_sec = models.IntegerField(null=True, blank=True)
    heartbeat_url = models.URLField(max_length=2048, null=True, blank=True)
    http_authentication_header = models.CharField(max_length=255, null=True, blank=True, default='')
    http_authentication_header_value = models.CharField(max_length=255, null=True, blank=True, default='')
    http_authentication_password = models.CharField(max_length=255, null=True, blank=True, default='')
    http_authentication_token_api_enabled = models.BooleanField(default=False)
    http_authentication_token_api_body = models.TextField(null=True, blank=True, default='')
    http_authentication_token_api_password_field = models.CharField(max_length=255, null=True, blank=True)
    http_authentication_token_api_password_value = models.CharField(max_length=255, null=True, blank=True)
    http_authentication_token_api_username_field = models.CharField(max_length=255, null=True, blank=True)
    http_authentication_token_api_username_value = models.CharField(max_length=255, null=True, blank=True)
    http_authentication_token_api_url = models.URLField(max_length=2048, null=True, blank=True, default='')
    http_authentication_token_api_value = models.TextField(null=True, blank=True, default='')
    http_authentication_type = models.CharField(max_length=50, null=True, blank=True, default='NONE')
    http_authentication_username = models.CharField(max_length=255, null=True, blank=True, default='')
    http_post_enabled = models.BooleanField(default=False)
    http_post_interval_sec = models.IntegerField(default=5)
    http_post_type = models.IntegerField(default=1)
    http_post_url = models.URLField(max_length=2048, default='http://server:8000/webhook/')
    http_verify_host = models.BooleanField(default=False)
    http_verify_peer = models.BooleanField(default=False)
    http_verify_post_http_return_code = models.BooleanField(default=False)
    include_antenna_port = models.BooleanField(default=True)
    include_antenna_zone = models.BooleanField(default=False)
    include_first_seen_timestamp = models.BooleanField(default=True)
    include_gpi_event = models.BooleanField(default=False)
    include_inventory_status_event = models.BooleanField(default=False)
    include_inventory_status_event_id = models.IntegerField(null=True, blank=True)
    include_inventory_status_event_total_count = models.IntegerField(null=True, blank=True)
    include_peak_rssi = models.BooleanField(default=False)
    include_reader_name = models.BooleanField(default=True)
    include_rf_channel_index = models.BooleanField(default=False)
    include_rf_doppler_frequency = models.BooleanField(default=False)
    include_rf_phase_angle = models.BooleanField(default=False)
    include_tid = models.BooleanField(default=False)
    include_user_memory = models.BooleanField(default=False)
    is_cloud_interface = models.BooleanField(default=False)
    is_current_profile = models.BooleanField(default=False)
    is_enabled = models.BooleanField(default=False)
    is_log_file_enabled = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    ip_address_mode = models.CharField(max_length=50, null=True, blank=True)
    ip_mask = models.GenericIPAddressField(null=True, blank=True)
    json_format = models.BooleanField(default=False)
    keep_filename_on_day_change = models.BooleanField(default=False)
    license_key = models.CharField(max_length=255)
    line_end = models.CharField(max_length=50, null=True, blank=True)
    low_duty_cycle_enabled = models.BooleanField(default=False)
    max_tx_power_on_gpi_event_enabled = models.BooleanField(default=False)
    mqtt_broker_address = models.GenericIPAddressField(null=True, blank=True)
    mqtt_broker_clean_session = models.BooleanField(default=True)
    mqtt_broker_debug = models.BooleanField(default=False)
    mqtt_broker_keep_alive = models.IntegerField(null=True, blank=True)
    mqtt_broker_name = models.CharField(max_length=255, null=True, blank=True, default='MQTT-SERVER')
    mqtt_broker_port = models.IntegerField(null=True, blank=True, default=1883)
    mqtt_broker_protocol = models.CharField(max_length=50, null=True, blank=True, default='tcp')
    mqtt_broker_type = models.CharField(max_length=50, null=True, blank=True)
    mqtt_broker_protocol = models.CharField(max_length=100, null=True, blank=True, default='/mqtt')
    mqtt_enabled = models.BooleanField(default=False)
    mqtt_control_command_qos = models.IntegerField(null=True, blank=True)
    mqtt_control_command_retain_messages = models.BooleanField(default=False)
    mqtt_control_command_topic = models.CharField(max_length=255, null=True, blank=True)
    mqtt_control_response_qos = models.IntegerField(null=True, blank=True)
    mqtt_control_response_topic = models.CharField(max_length=255, null=True, blank=True)
    mqtt_lwt_qos = models.IntegerField(null=True, blank=True)
    mqtt_lwt_topic = models.CharField(max_length=255, null=True, blank=True)
    mqtt_management_command_qos = models.IntegerField(null=True, blank=True)
    mqtt_management_command_retain_messages = models.BooleanField(default=False)
    mqtt_management_command_topic = models.CharField(max_length=255, null=True, blank=True)
    mqtt_management_response_qos = models.IntegerField(null=True, blank=True)
    mqtt_management_response_topic = models.CharField(max_length=255, null=True, blank=True)
    mqtt_management_events_qos = models.IntegerField(null=True, blank=True)
    mqtt_management_events_retain_messages = models.BooleanField(default=False)
    mqtt_management_events_topic = models.CharField(max_length=255, null=True, blank=True)
    mqtt_metric_events_qos = models.IntegerField(null=True, blank=True)
    mqtt_metric_events_topic = models.CharField(max_length=255, null=True, blank=True)
    mqtt_password = models.CharField(max_length=255, null=True, blank=True)
    mqtt_proxy_password = models.CharField(max_length=255, null=True, blank=True)
    mqtt_proxy_url = models.URLField(max_length=2048, null=True, blank=True)
    mqtt_proxy_username = models.CharField(max_length=255, null=True, blank=True)
    mqtt_publish_interval_sec = models.IntegerField(null=True, blank=True)
    mqtt_ssl_ca_certificate = models.TextField(null=True, blank=True)
    mqtt_ssl_client_certificate = models.TextField(null=True, blank=True)
    mqtt_ssl_client_certificate_password = models.CharField(max_length=255, null=True, blank=True)
    mqtt_tag_events_qos = models.IntegerField(null=True, blank=True)
    mqtt_tag_events_retain_messages = models.BooleanField(default=False)
    mqtt_tag_events_topic = models.CharField(max_length=255, null=True, blank=True)
    mqtt_username = models.CharField(max_length=255, null=True, blank=True)
    mqtt_use_ssl = models.BooleanField(default=False)
    network_proxy = models.CharField(max_length=255, null=True, blank=True)
    network_proxy_port = models.IntegerField(null=True, blank=True)
    enable_opc_ua_client = models.BooleanField(default=False)
    opc_ua_connection_discovery_address = models.URLField(max_length=2048, null=True, blank=True)
    opc_ua_connection_name = models.CharField(max_length=255, null=True, blank=True)
    opc_ua_connection_publisher_id = models.IntegerField(null=True, blank=True)
    opc_ua_connection_url = models.URLField(max_length=2048, null=True, blank=True)
    opc_ua_data_set_key_frame_count = models.IntegerField(null=True, blank=True)
    opc_ua_data_set_name = models.CharField(max_length=255, null=True, blank=True)
    opc_ua_data_set_writer_id = models.IntegerField(null=True, blank=True)
    opc_ua_data_set_writer_name = models.CharField(max_length=255, null=True, blank=True)
    opc_ua_writer_group_id = models.IntegerField(null=True, blank=True)
    opc_ua_writer_group_name = models.CharField(max_length=255, null=True, blank=True)
    opc_ua_writer_header_layout_uri = models.CharField(max_length=255, null=True, blank=True)
    opc_ua_writer_keep_alive_time = models.IntegerField(null=True, blank=True)
    opc_ua_writer_max_network_message_size = models.IntegerField(null=True, blank=True)
    opc_ua_writer_publishing_interval = models.IntegerField(null=True, blank=True)
    operating_region = models.CharField(max_length=255, null=True, blank=True)
    package_headers = models.CharField(max_length=255, null=True, blank=True)
    parse_sgtin_enabled = models.BooleanField(default=False)
    parse_sgtin_include_key_type = models.BooleanField(default=False)
    parse_sgtin_include_pure_identity = models.BooleanField(default=False)
    parse_sgtin_include_serial = models.BooleanField(default=False)
    plugin_server = models.CharField(max_length=255, null=True, blank=True)
    positioning_antenna_ports = models.CharField(max_length=255, null=True, blank=True)
    positioning_epcs_enabled = models.BooleanField(default=False)
    positioning_epcs_filter = models.CharField(max_length=255, null=True, blank=True)
    positioning_epcs_header_list = models.CharField(max_length=255, null=True, blank=True)
    positioning_expiration_in_sec = models.IntegerField(null=True, blank=True)
    positioning_report_interval_in_sec = models.IntegerField(null=True, blank=True)
    profile_name = models.CharField(max_length=255)
    prompt_before_changing = models.BooleanField(default=False)
    publish_full_shipment_validation_list_on_acceptance_threshold = models.BooleanField(default=False)
    publish_single_time_on_acceptance_threshold = models.BooleanField(default=False)
    rci_spot_report_enabled = models.BooleanField(default=False)
    rci_spot_report_include_ant = models.BooleanField(default=False)
    rci_spot_report_include_dwn_cnt = models.BooleanField(default=False)
    rci_spot_report_include_epc_uri = models.BooleanField(default=False)
    rci_spot_report_include_inv_cnt = models.BooleanField(default=False)
    rci_spot_report_include_pc = models.BooleanField(default=False)
    rci_spot_report_include_phase = models.BooleanField(default=False)
    rci_spot_report_include_prof = models.BooleanField(default=False)
    rci_spot_report_include_range = models.BooleanField(default=False)
    rci_spot_report_include_rssi = models.BooleanField(default=False)
    rci_spot_report_include_rz = models.BooleanField(default=False)
    rci_spot_report_include_scheme = models.BooleanField(default=False)
    rci_spot_report_include_spot = models.BooleanField(default=False)
    rci_spot_report_include_time_stamp = models.BooleanField(default=False)
    reader_mode = models.IntegerField(default=3)
    reader_name = models.CharField(max_length=255)
    reader_serial = models.CharField(max_length=255)
    receive_sensitivity = models.CharField(max_length=255, default='-92,-92,-92,-92')
    reporting_interval_seconds = models.IntegerField(null=True, blank=True)
    require_unique_product_code = models.BooleanField(default=False)
    search_mode = models.IntegerField(default=1)
    serial_port = models.CharField(max_length=255, null=True, blank=True)
    session = models.IntegerField(default=1)
    site = models.CharField(max_length=255, null=True, blank=True)
    site_enabled = models.BooleanField(default=False)
    smartreader_enabled_for_management_only = models.BooleanField(default=False)
    socket_command_server = models.BooleanField(default=False)
    socket_command_server_port = models.IntegerField(default=14151)
    socket_port = models.IntegerField(default=14150)
    socket_server = models.BooleanField(default=False)
    software_filter_enabled = models.BooleanField(default=False)
    software_filter_field = models.IntegerField(null=True, blank=True)
    software_filter_include_epcs_header_list = models.CharField(max_length=255, null=True, blank=True)
    software_filter_include_epcs_header_list_enabled = models.BooleanField(default=False)
    software_filter_read_count_timeout_enabled = models.BooleanField(default=False)
    software_filter_read_count_timeout_interval_in_sec = models.IntegerField(null=True, blank=True)
    software_filter_read_count_timeout_seen_count = models.IntegerField(null=True, blank=True)
    software_filter_tag_id_enabled = models.BooleanField(default=False)
    software_filter_tag_id_match = models.CharField(max_length=255, null=True, blank=True)
    software_filter_tag_id_operation = models.CharField(max_length=255, null=True, blank=True)
    software_filter_tag_id_value_or_pattern = models.CharField(max_length=255, null=True, blank=True)
    software_filter_window_sec = models.IntegerField(null=True, blank=True)
    start_trigger_gpi_event = models.IntegerField(default=1)
    start_trigger_gpi_port = models.IntegerField(default=1)
    start_trigger_offset = models.IntegerField(default=0)
    start_trigger_period = models.IntegerField(default=0)
    start_trigger_type = models.IntegerField(default=1)
    start_trigger_utc_timestamp = models.IntegerField(default=0)
    stop_trigger_duration = models.IntegerField(default=0)
    stop_trigger_gpi_event = models.IntegerField(default=0)
    stop_trigger_gpi_port = models.IntegerField(default=1)
    stop_trigger_timeout = models.IntegerField(default=0)
    stop_trigger_type = models.IntegerField(default=0)
    system_disable_image_fallback_status = models.BooleanField(default=False)
    system_image_upgrade_url = models.URLField(max_length=2048, null=True, blank=True)
    tag_cache_size = models.IntegerField(null=True, blank=True)
    tag_identifier = models.CharField(max_length=255, null=True, blank=True)
    tag_population = models.IntegerField(default=32)
    tag_presence_timeout_enabled = models.BooleanField(default=False)
    tag_presence_timeout_in_sec = models.IntegerField(null=True, blank=True)
    tag_validation_enabled = models.BooleanField(default=False)
    tid_word_count = models.IntegerField(null=True, blank=True)
    tid_word_start = models.IntegerField(null=True, blank=True)
    toi_gpi = models.IntegerField(null=True, blank=True)
    toi_gpo_error = models.IntegerField(null=True, blank=True)
    toi_gpo_mode = models.IntegerField(null=True, blank=True)
    toi_gpo_nok = models.IntegerField(null=True, blank=True)
    toi_gpo_ok = models.IntegerField(null=True, blank=True)
    toi_gpo_priority = models.IntegerField(null=True, blank=True)
    toi_validation_enabled = models.BooleanField(default=False)
    toi_validation_gpo_duration = models.IntegerField(null=True, blank=True)
    toi_validation_url = models.URLField(max_length=2048, null=True, blank=True)
    transmit_power = models.CharField(max_length=255, default='1500,1500,1500,1500')
    truncate_epc = models.BooleanField(default=False)
    truncate_len = models.IntegerField(null=True, blank=True)
    truncate_start = models.IntegerField(null=True, blank=True)
    udp_ip_address = models.GenericIPAddressField(null=True, blank=True)
    udp_reader_port = models.IntegerField(null=True, blank=True, default=11000)
    udp_remote_ip_address = models.GenericIPAddressField(null=True, blank=True)
    udp_remote_port = models.IntegerField(null=True, blank=True, default=10000)
    udp_server = models.BooleanField(default=False)
    update_tag_events_list_batch_on_change = models.BooleanField(default=False)
    update_tag_events_list_batch_on_change_interval_in_sec = models.IntegerField(null=True, blank=True)
    usb_flash_drive = models.BooleanField(default=False)
    usb_hid = models.BooleanField(default=False)
    user_memory_word_count = models.IntegerField(null=True, blank=True)
    user_memory_word_start = models.IntegerField(null=True, blank=True)
    validation_acceptance_threshold = models.IntegerField(null=True, blank=True)
    validation_acceptance_threshold_timeout = models.IntegerField(null=True, blank=True)
    write_usb_json = models.BooleanField(default=False)

    C1G2_BANK_FILTER_CHOICES = [
        (0, 'Reserved'),
        (1, 'EPC'),
        (2, 'TID'),
        (3, 'User'),
    ]
    READER_MODE_CHOICES = [
        (0, 'High Throughput'),
        (1, 'Hybrid'),
        (2, 'Dense Reader M4'),
        (3, 'Dense Reader M8'),
        (4, 'Max Miller'),
        (5, 'Max Miller ETSI'),
        (1002, 'Autoset Dense Reader Deep Scan'),
        (1003, 'Autoset Static Fast'),
        (1004, 'Autoset Static Dense Reader'),
    ]
    SEARCH_MODE_CHOICES = [
        (0, 'Reader Selected'),
        (1, 'Single Target'),
        (2, 'Dual Target'),
        (3, 'TagFocus'),
        (5, 'Single Target Reset'),
        (6, 'Dual Target BtoA Select'),
    ]
    ADVANCED_GPO_CHOICES = [
        (0, 'Normal'),
        (4, 'Reader Inventory Status'),
        (6, 'New Tag Seen'),
        (9, 'Any Tag Seen'),
        (10, 'On Error Status'),
        (11, 'On Network Error Status'),
        (7, 'Success on Rule Validation'),
        (8, 'Error on Rule Validation'),
    ]
    START_TRIGGER_CHOICES = [
        (1, 'Immediate'),
        (3, 'GPI'),
        (4, 'Barcode'),
    ]
    START_TRIGGER_GPI_PORT_CHOICES = [
        (0, 'Disabled'),
        (1, '1'),
        (2, '2'),
    ]
    START_TRIGGER_GPI_EVENT_CHOICES = [
        (0, 'Low'),
        (1, 'High'),
    ]
    STOP_TRIGGER_CHOICES = [
        (0, 'None'),
        (1, 'Duration'),
        (2, 'GPI'),
    ]
    STOP_TRIGGER_GPI_PORT_CHOICES = [
        (0, 'Disabled'),
        (1, '1'),
        (2, '2'),
    ]
    STOP_TRIGGER_GPI_EVENT_CHOICES = [
        (0, 'Low'),
        (1, 'High'),
    ]

    def __str__(self):
        return self.reader_serial

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

    def populate_mqtt_from_configuration(self, mqtt_config):
        """Populates the MQTT fields based on an MQTTConfiguration instance."""
        self.mqtt_enabled = mqtt_config.enable_mqtt
        self.mqtt_use_ssl = mqtt_config.enable_command_receiver  # Assuming this field should be mapped, adjust if needed
        self.mqtt_ssl_ca_certificate = ""  # Populate from configuration if needed
        self.mqtt_ssl_client_certificate = ""  # Populate from configuration if needed
        self.mqtt_ssl_client_certificate_password = ""  # Populate from configuration if needed
        self.mqtt_broker_name = mqtt_config.broker_hostname
        self.mqtt_broker_address = mqtt_config.broker_hostname
        self.mqtt_broker_port = mqtt_config.broker_port
        self.mqtt_broker_clean_session = mqtt_config.mqtt_broker_clean_session
        self.mqtt_broker_keep_alive = mqtt_config.mqtt_broker_keepalive

        self.mqtt_tag_events_topic = f"{mqtt_config.tag_events_topic.replace('smartreader/', f'smartreader/{self.reader_serial}/')}"
        self.mqtt_tag_events_qos = mqtt_config.tag_events_qos_level
        self.mqtt_tag_events_retain_messages = mqtt_config.tag_events_retain

        self.mqtt_management_events_topic = f"{mqtt_config.management_events_topic.replace('smartreader/', f'smartreader/{self.reader_serial}/')}"
        self.mqtt_management_events_qos = mqtt_config.management_events_qos_level
        self.mqtt_management_events_retain_messages = mqtt_config.management_events_retain

        self.mqtt_metric_events_topic = f"{mqtt_config.metrics_topic.replace('smartreader/', f'smartreader/{self.reader_serial}/')}"
        self.mqtt_metric_events_qos = mqtt_config.metrics_qos_level
        self.mqtt_metric_events_retain_messages = mqtt_config.metrics_retain

        self.mqtt_management_command_topic = f"{mqtt_config.management_command_topic.replace('smartreader/', f'smartreader/{self.reader_serial}/')}"
        self.mqtt_management_command_qos = mqtt_config.management_command_qos_level
        self.mqtt_management_command_retain_messages = mqtt_config.management_command_retain

        self.mqtt_management_response_topic = f"{mqtt_config.management_command_response_topic.replace('smartreader/', f'smartreader/{self.reader_serial}/')}"
        self.mqtt_management_response_qos = mqtt_config.management_command_response_qos_level
        self.mqtt_management_response_retain_messages = mqtt_config.management_command_retain

        self.mqtt_control_command_topic = f"{mqtt_config.control_command_topic.replace('smartreader/', f'smartreader/{self.reader_serial}/')}"
        self.mqtt_control_command_qos = mqtt_config.control_command_qos_level
        self.mqtt_control_command_retain_messages = mqtt_config.control_command_retain

        self.mqtt_control_response_topic = f"{mqtt_config.control_command_response_topic.replace('smartreader/', f'smartreader/{self.reader_serial}/')}"
        self.mqtt_control_response_qos = mqtt_config.control_command_response_qos_level
        self.mqtt_control_response_retain_messages = mqtt_config.control_command_retain

        self.mqtt_lwt_topic = mqtt_config.mqtt_lwt_topic.replace('{deviceId}', self.reader_serial)
        self.mqtt_lwt_qos = mqtt_config.mqtt_lwt_qos_level

        self.mqtt_username = mqtt_config.broker_username
        self.mqtt_password = mqtt_config.broker_password
        self.mqtt_enable_smartreader_default_topics = mqtt_config.enable_command_receiver

    JSON_FIELD_MAP = {
        "activePlugin": "active_plugin",
        "advancedGpoEnabled": "advanced_gpo_enabled",
        "advancedGpoMode1": "advanced_gpo_mode_1",
        "advancedGpoMode2": "advanced_gpo_mode_2",
        "advancedGpoMode3": "advanced_gpo_mode_3",
        "advancedGpoMode4": "advanced_gpo_mode_4",
        "antennaIdentifier": "antenna_identifier",
        "antennaPorts": "antenna_ports",
        "antennaStates": "antenna_states",
        "antennaZones": "antenna_zones",
        "applyIpSettingsOnStartup": "apply_ip_settings_on_startup",
        "backupToFlashDriveOnGpiEventEnabled": "backup_to_flash_drive_on_gpi_event_enabled",
        "backupToInternalFlashEnabled": "backup_to_internal_flash_enabled",
        "barcodeEnableQueue": "barcode_enable_queue",
        "barcodeLineEnd": "barcode_line_end",
        "barcodeNoDataString": "barcode_no_data_string",
        "barcodeProcessNoDataString": "barcode_process_no_data_string",
        "barcodeTcpAddress": "barcode_tcp_address",
        "barcodeTcpLen": "barcode_tcp_len",
        "barcodeTcpNoDataString": "barcode_tcp_no_data_string",
        "barcodeTcpPort": "barcode_tcp_port",
        "baudRate": "baud_rate",
        "broadcastAddress": "broadcast_address",
        "c1g2FilterEnabled": "c1g2_filter_enabled",
        "c1g2FilterBank": "c1g2_filter_bank",
        "c1g2FilterLen": "c1g2_filter_len",
        "c1g2FilterMask": "c1g2_filter_mask",
        "c1g2FilterMatchOption": "c1g2_filter_match_option",
        "c1g2FilterPointer": "c1g2_filter_pointer",
        "cleanupTagEventsListBatchOnReload": "cleanup_tag_events_list_batch_on_reload",
        "connectionStatus": "connection_status",
        "csvFileFormat": "csv_file_format",
        "customField1Enabled": "custom_field_1_enabled",
        "customField1Name": "custom_field_1_name",
        "customField1Value": "custom_field_1_value",
        "customField2Enabled": "custom_field_2_enabled",
        "customField2Name": "custom_field_2_name",
        "customField2Value": "custom_field_2_value",
        "customField3Enabled": "custom_field_3_enabled",
        "customField3Name": "custom_field_3_name",
        "customField3Value": "custom_field_3_value",
        "customField4Enabled": "custom_field_4_enabled",
        "customField4Name": "custom_field_4_name",
        "customField4Value": "custom_field_4_value",
        "dataPrefix": "data_prefix",
        "dataSuffix": "data_suffix",
        "emptyFieldTimeout": "empty_field_timeout",
        "enableAntennaTask": "enable_antenna_task",
        "enableBarcodeHid": "enable_barcode_hid",
        "enableBarcodeSerial": "enable_barcode_serial",
        "enableOpcUaClient": "enable_barcode_tcp",
        "enablePartialValidation": "enable_external_api_verification",
        "enablePlugin": "enable_plugin",
        "enablePluginShipmentVerification": "enable_plugin_shipment_verification",
        "enablePartialValidation": "enable_partial_validation",
        "enableSmartreaderDefaultTopics": "mqtt_enable_smartreader_default_topics",
        "enableSummaryStream": "enable_summary_stream",
        "enableTagEventStream": "enable_tag_event_stream",
        "enableTagEventsListBatch": "enable_tag_events_list_batch",
        "enableTagEventsListBatchPublishing": "enable_tag_events_list_batch_publishing",
        "enableUniqueTagRead": "enable_unique_tag_read",
        "enableValidation": "enable_validation",
        "externalApiVerificationAuthLoginUrl": "external_api_verification_auth_login_url",
        "externalApiVerificationChangeOrderStatusUrl": "external_api_verification_change_order_status_url",
        "externalApiVerificationHttpHeaderName": "external_api_verification_http_header_name",
        "externalApiVerificationHttpHeaderValue": "external_api_verification_http_header_value",
        "externalApiVerificationPublishDataUrl": "external_api_verification_publish_data_url",
        "externalApiVerificationSearchOrderUrl": "external_api_verification_search_order_url",
        "externalApiVerificationSearchProductUrl": "external_api_verification_search_product_url",
        "filterTagEventsListBatchOnChangeBasedOnAntennaZone": "filter_tag_events_list_batch_on_change_based_on_antenna_zone",
        "fieldDelim": "field_delim",
        "fieldPingInterval": "field_ping_interval",
        "gatewayAddress": "gateway_address",
        "groupEventsOnInventoryStatus": "group_events_on_inventory_status",
        "gtinOutputType": "gtin_output_type",
        "heartbeatEnabled": "heartbeat_enabled",
        "heartbeatHttpAuthenticationUsername": "heartbeat_http_authentication_username",
        "heartbeatHttpAuthenticationPassword": "heartbeat_http_authentication_password",
        "heartbeatHttpAuthenticationTokenApiBody": "heartbeat_http_authentication_token_api_body",
        "heartbeatHttpAuthenticationTokenApiEnabled": "heartbeat_http_authentication_token_api_enabled",
        "heartbeatHttpAuthenticationTokenApiPasswordField": "heartbeat_http_authentication_token_api_password_field",
        "heartbeatHttpAuthenticationTokenApiPasswordValue": "heartbeat_http_authentication_token_api_password_value",
        "heartbeatHttpAuthenticationTokenApiUsernameField": "heartbeat_http_authentication_token_api_username_field",
        "heartbeatHttpAuthenticationTokenApiUsernameValue": "heartbeat_http_authentication_token_api_username_value",
        "heartbeatHttpAuthenticationTokenApiUrl": "heartbeat_http_authentication_token_api_url",
        "heartbeatHttpAuthenticationTokenApiValue": "heartbeat_http_authentication_token_api_value",
        "heartbeatHttpAuthenticationType": "heartbeat_http_authentication_type",
        "heartbeatPeriodSec": "heartbeat_period_sec",
        "heartbeatUrl": "heartbeat_url",
        "httpAuthenticationHeader": "http_authentication_header",
        "httpAuthenticationHeaderValue": "http_authentication_header_value",
        "httpAuthenticationPassword": "http_authentication_password",
        "httpAuthenticationTokenApiEnabled": "http_authentication_token_api_enabled",
        "httpAuthenticationTokenApiBody": "http_authentication_token_api_body",
        "httpAuthenticationTokenApiPasswordField": "http_authentication_token_api_password_field",
        "httpAuthenticationTokenApiPasswordValue": "http_authentication_token_api_password_value",
        "httpAuthenticationTokenApiUsernameField": "http_authentication_token_api_username_field",
        "httpAuthenticationTokenApiUsernameValue": "http_authentication_token_api_username_value",
        "httpAuthenticationTokenApiUrl": "http_authentication_token_api_url",
        "httpAuthenticationTokenApiValue": "http_authentication_token_api_value",
        "httpAuthenticationType": "http_authentication_type",
        "httpAuthenticationUsername": "http_authentication_username",
        "httpPostEnabled": "http_post_enabled",
        "httpPostIntervalSec": "http_post_interval_sec",
        "httpPostType": "http_post_type",
        "httpPostURL": "http_post_url",
        "httpVerifyHost": "http_verify_host",
        "httpVerifyPeer": "http_verify_peer",
        "httpVerifyPostHttpReturnCode": "http_verify_post_http_return_code",
        "includeAntennaPort": "include_antenna_port",
        "includeAntennaZone": "include_antenna_zone",
        "includeFirstSeenTimestamp": "include_first_seen_timestamp",
        "includeGpiEvent": "include_gpi_event",
        "includeInventoryStatusEvent": "include_inventory_status_event",
        "includeInventoryStatusEventId": "include_inventory_status_event_id",
        "includeInventoryStatusEventTotalCount": "include_inventory_status_event_total_count",
        "includePeakRssi": "include_peak_rssi",
        "includeReaderName": "include_reader_name",
        "includeRFChannelIndex": "include_rf_channel_index",
        "includeRFDopplerFrequency": "include_rf_doppler_frequency",
        "includeRFPhaseAngle": "include_rf_phase_angle",
        "includeTid": "include_tid",
        "includeUserMemory": "include_user_memory",
        "isCloudInterface": "is_cloud_interface",
        "isCurrentProfile": "is_current_profile",
        "isEnabled": "is_enabled",
        "isLogFileEnabled": "is_log_file_enabled",
        "ipAddress": "ip_address",
        "ipAddressMode": "ip_address_mode",
        "ipMask": "ip_mask",
        "jsonFormat": "json_format",
        "keepFilenameOnDayChange": "keep_filename_on_day_change",
        "licenseKey": "license_key",
        "lineEnd": "line_end",
        "lowDutyCycleEnabled": "low_duty_cycle_enabled",
        "maxTxPowerOnGpiEventEnabled": "max_tx_power_on_gpi_event_enabled",
        "mqttBrokerAddress": "mqtt_broker_address",
        "mqttBrokerCleanSession": "mqtt_broker_clean_session",
        "mqttBrokerDebug": "mqtt_broker_debug",
        "mqttBrokerKeepAlive": "mqtt_broker_keep_alive",
        "mqttBrokerName": "mqtt_broker_name",
        "mqttBrokerPort": "mqtt_broker_port",
        "mqttBrokerProtocol": "mqtt_broker_protocol",
        "mqttBrokerType": "mqtt_broker_type",
        "mqttBrokerWebSocketPath": "mqtt_broker_protocol",
        "mqttEnabled": "mqtt_enabled",
        "mqttControlCommandQoS": "mqtt_control_command_qos",
        "mqttControlCommandRetainMessages": "mqtt_control_command_retain_messages",
        "mqttControlCommandTopic": "mqtt_control_command_topic",
        "mqttControlResponseQoS": "mqtt_control_response_qos",
        "mqttControlResponseTopic": "mqtt_control_response_topic",
        "mqttLwtQoS": "mqtt_lwt_qos",
        "mqttLwtTopic": "mqtt_lwt_topic",
        "mqttManagementCommandQoS": "mqtt_management_command_qos",
        "mqttManagementCommandRetainMessages": "mqtt_management_command_retain_messages",
        "mqttManagementCommandTopic": "mqtt_management_command_topic",
        "mqttManagementEventsQoS": "mqtt_management_response_qos",
        "mqttManagementEventsRetainMessages": "mqtt_management_response_topic",
        "mqttManagementEventsTopic": "mqtt_management_events_qos",
        "mqttManagementResponseQoS": "mqtt_management_events_retain_messages",
        "mqttManagementResponseTopic": "mqtt_management_events_topic",
        "mqttMetricEventsQoS": "mqtt_metric_events_qos",
        "mqttMetricEventsTopic": "mqtt_metric_events_topic",
        "mqttPassword": "mqtt_password",
        "mqttProxyPassword": "mqtt_proxy_password",
        "mqttProxyUrl": "mqtt_proxy_url",
        "mqttProxyUsername": "mqtt_proxy_username",
        "mqttPuslishIntervalSec": "mqtt_publish_interval_sec",
        "mqttSslCaCertificate": "mqtt_ssl_ca_certificate",
        "mqttSslClientCertificate": "mqtt_ssl_client_certificate",
        "mqttSslClientCertificatePassword": "mqtt_ssl_client_certificate_password",
        "mqttTagEventsQoS": "mqtt_tag_events_qos",
        "mqttTagEventsRetainMessages": "mqtt_tag_events_retain_messages",
        "mqttTagEventsTopic": "mqtt_tag_events_topic",
        "mqttUsername": "mqtt_username",
        "mqttUseSsl": "mqtt_use_ssl",
        "networkProxy": "network_proxy",
        "networkProxyPort": "network_proxy_port",
        "enableOpcUaClient": "enable_opc_ua_client",
        "opcUaConnectionDiscoveryAddress": "opc_ua_connection_discovery_address",
        "opcUaConnectionName": "opc_ua_connection_name",
        "opcUaConnectionPublisherId": "opc_ua_connection_publisher_id",
        "opcUaConnectionUrl": "opc_ua_connection_url",
        "opcUaDataSetKeyFrameCount": "opc_ua_data_set_key_frame_count",
        "opcUaDataSetName": "opc_ua_data_set_name",
        "opcUaDataSetWriterId": "opc_ua_data_set_writer_id",
        "opcUaDataSetWriterName": "opc_ua_data_set_writer_name",
        "opcUaWriterGroupId": "opc_ua_writer_group_id",
        "opcUaWriterGroupName": "opc_ua_writer_group_name",
        "opcUaWriterHeaderLayoutUri": "opc_ua_writer_header_layout_uri",
        "opcUaWriterKeepAliveTime": "opc_ua_writer_keep_alive_time",
        "opcUaWriterMaxNetworkMessageSize": "opc_ua_writer_max_network_message_size",
        "opcUaWriterPublishingInterval": "opc_ua_writer_publishing_interval",
        "operatingRegion": "operating_region",
        "packageHeaders": "package_headers",
        "parseSgtinEnabled": "parse_sgtin_enabled",
        "parseSgtinIncludeKeyType": "parse_sgtin_include_key_type",
        "parseSgtinIncludePureIdentity": "parse_sgtin_include_pure_identity",
        "parseSgtinIncludeSerial": "parse_sgtin_include_serial",
        "pluginServer": "plugin_server",
        "positioningAntennaPorts": "positioning_antenna_ports",
        "positioningEpcsEnabled": "positioning_epcs_enabled",
        "positioningEpcsFilter": "positioning_epcs_filter",
        "positioningEpcsHeaderList": "positioning_epcs_header_list",
        "positioningExpirationInSec": "positioning_expiration_in_sec",
        "positioningReportIntervalInSec": "positioning_report_interval_in_sec",
        "profileName": "profile_name",
        "promptBeforeChanging": "prompt_before_changing",
        "publishFullShipmentValidationListOnAcceptanceThreshold": "publish_full_shipment_validation_list_on_acceptance_threshold",
        "publishSingleTimeOnAcceptanceThreshold,": "publish_single_time_on_acceptance_threshold",
        "rciSpotReportEnabled": "rci_spot_report_enabled",
        "rciSpotReportIncludeAnt": "rci_spot_report_include_ant",
        "rciSpotReportIncludeDwnCnt": "rci_spot_report_include_dwn_cnt",
        "rciSpotReportIncludeEpcUri": "rci_spot_report_include_epc_uri",
        "rciSpotReportIncludeInvCnt": "rci_spot_report_include_inv_cnt",
        "rciSpotReportIncludePc": "rci_spot_report_include_pc",
        "rciSpotReportIncludePhase": "rci_spot_report_include_phase",
        "rciSpotReportIncludeProf": "rci_spot_report_include_prof",
        "rciSpotReportIncludeRange": "rci_spot_report_include_range",
        "rciSpotReportIncludeRssi": "rci_spot_report_include_rssi",
        "rciSpotReportIncludeRz": "rci_spot_report_include_rz",
        "rciSpotReportIncludeScheme": "rci_spot_report_include_scheme",
        "rciSpotReportIncludeSpot": "rci_spot_report_include_spot",
        "rciSpotReportIncludeTimeStamp": "rci_spot_report_include_time_stamp",
        "readerMode": "reader_mode",
        "readerName": "reader_name",
        "readerSerial": "reader_serial",
        "receiveSensitivity": "receive_sensitivity",
        "reportIntervalInSec": "reporting_interval_seconds",
        "requireUniqueProductCode": "require_unique_product_code",
        "searchMode": "search_mode",
        "serialPort": "serial_port",
        "session": "session",
        "site": "site",
        "siteEnabled": "site_enabled",
        "smartreaderEnabledForManagementOnly": "smartreader_enabled_for_management_only",
        "socketCommandServer": "socket_command_server",
        "socketCommandServerPort": "socket_command_server_port",
        "socketServer": "socket_port",
        "socketPort": "socket_server",
        "softwareFilterEnabled": "software_filter_enabled",
        "softwareFilterField": "software_filter_field",
        "softwareFilterIncludeEpcsHeaderList": "software_filter_include_epcs_header_list",
        "softwareFilterIncludeEpcsHeaderListEnabled": "software_filter_include_epcs_header_list_enabled",
        "softwareFilterReadCountTimeoutEnabled": "software_filter_read_count_timeout_enabled",
        "softwareFilterReadCountTimeoutIntervalInSec": "software_filter_read_count_timeout_interval_in_sec",
        "softwareFilterReadCountTimeoutSeenCount": "software_filter_read_count_timeout_seen_count",
        "softwareFilterTagIdEnabled": "software_filter_tag_id_enabled",
        "softwareFilterTagIdMatch": "software_filter_tag_id_match",
        "softwareFilterTagIdOperation": "software_filter_tag_id_operation",
        "softwareFilterTagIdValueOrPattern": "software_filter_tag_id_value_or_pattern",
        "softwareFilterWindowSec": "software_filter_window_sec",
        "startTriggerGpiEvent": "start_trigger_gpi_event",
        "startTriggerGpiPort": "start_trigger_gpi_port",
        "startTriggerOffset": "start_trigger_offset",
        "startTriggerPeriod": "start_trigger_period",
        "startTriggerType": "start_trigger_type",
        "startTriggerUTCTimestamp": "start_trigger_utc_timestamp",
        "stopTriggerDuration": "stop_trigger_duration",
        "stopTriggerGpiEvent": "stop_trigger_gpi_event",
        "stopTriggerGpiPort": "stop_trigger_gpi_port",
        "stopTriggerTimeout": "stop_trigger_timeout",
        "stopTriggerType": "stop_trigger_type",
        "systemDisableImageFallbackStatus": "system_disable_image_fallback_status",
        "systemImageUpgradeUrl": "system_image_upgrade_url",
        "tagCacheSize": "tag_cache_size",
        "tagIdentifier": "tag_identifier",
        "tagPopulation": "tag_population",
        "tagPresenceTimeoutEnabled": "tag_presence_timeout_enabled",
        "tagPresenceTimeoutInSec": "tag_presence_timeout_in_sec",
        "tagValidationEnabled": "tag_validation_enabled",
        "tidWordCount": "tid_word_count",
        "tidWordStart": "tid_word_start",
        "toiGpi": "toi_gpi",
        "toiGpoError": "toi_gpo_error",
        "toiGpoMode": "toi_gpo_mode",
        "toiGpoNok": "toi_gpo_nok",
        "toiGpoOk": "toi_gpo_ok",
        "toiGpoPriority": "toi_gpo_priority",
        "toiValidationEnabled": "toi_validation_enabled",
        "toiValidationGpoDuration": "toi_validation_gpo_duration",
        "toiValidationUrl": "toi_validation_url",
        "transmitPower": "transmit_power",
        "truncateEpc": "truncate_epc",
        "truncateLen": "truncate_len",
        "truncateStart": "truncate_start",
        "udpIpAddress": "udp_ip_address",
        "udpReaderPort": "udp_reader_port",
        "udpRemoteIpAddress": "udp_remote_ip_address",
        "udpRemotePort": "udp_remote_port",
        "udpServer": "udp_server",
        "updateTagEventsListBatchOnChange": "update_tag_events_list_batch_on_change",
        "updateTagEventsListBatchOnChangeIntervalInSec": "update_tag_events_list_batch_on_change_interval_in_sec",
        "usbFlashDrive": "usb_flash_drive",
        "usbHid": "usb_hid",
        "userMemoryWordCount": "user_memory_word_count",
        "userMemoryWordStart": "user_memory_word_start",
        "validationAcceptanceThreshold": "validation_acceptance_threshold",
        "validationAcceptanceThresholdTimeout": "validation_acceptance_threshold_timeout",
        "writeUsbJson": "write_usb_json"
    }
    def to_json(self):
        json_data = {}
        
        try:
            # Iterates over all fields of the class and maps them to JSON
            for field in self._meta.fields:
                try:
                    value = getattr(self, field.name)
                    json_key = next((k for k, v in self.JSON_FIELD_MAP.items() if v == field.name), field.name)

                    if isinstance(value, bool):
                        json_data[json_key] = "1" if value else "0"
                    else:
                        json_data[json_key] = str(value) if value is not None else ""
                except AttributeError as e:
                    logger.error(f"AttributeError: Failed to get value for field '{field.name}'. Error: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error when processing field '{field.name}'. Error: {e}")

            return json.dumps(json_data)

        except Exception as e:
            logger.error(f"Failed to convert model to JSON. Error: {e}")
            return {}

    @classmethod
    def from_json(cls, json_str):
        try:
            data = json.loads(json_str)
            obj = cls()

            # Iterates over the JSON_FIELD_MAP dictionary to map the JSON back to the model
            for json_key, field_name in cls.JSON_FIELD_MAP.items():
                if json_key in data:
                    try:
                        value = data[json_key]
                        field = cls._meta.get_field(field_name)

                        if isinstance(field, models.BooleanField):
                            setattr(obj, field_name, value == "1")
                        else:
                            setattr(obj, field_name, value)
                    except FieldDoesNotExist as e:
                        logger.error(f"FieldDoesNotExist: Field '{field_name}' does not exist. Error: {e}")
                    except Exception as e:
                        logger.error(f"Unexpected error when mapping JSON key '{json_key}' to field '{field_name}'. Error: {e}")

            return obj

        except json.JSONDecodeError as e:
            logger.error(f"JSONDecodeError: Invalid JSON string. Error: {e}")
        except Exception as e:
            logger.error(f"Failed to convert JSON to model. Error: {e}")

        return None
    
class MqttCommandTemplate(models.Model):
    COMMAND_TYPE_CONTROL = 'control'
    COMMAND_TYPE_MANAGEMENT = 'management'

    COMMAND_TYPE_CHOICES = [
        (COMMAND_TYPE_CONTROL, 'Control'),
        (COMMAND_TYPE_MANAGEMENT, 'Management'),
    ]

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    template_content = models.JSONField(default=dict)  # Store the command template as JSON
    command_type = models.CharField(max_length=20, choices=COMMAND_TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def apply_to_smartreader(self, smartreader):
        """
        Apply this template to a given SmartReader instance.
        Replace tags in the JSON content with actual SmartReader data.
        """
        template_str = json.dumps(self.template_content)
        # Define the replacements using SmartReader fields
        replacements = {
            "{{reader_serial}}": smartreader.reader_serial,
            "{{mqtt_broker_name}}": smartreader.mqtt_broker_name,
            # Add more replacements as needed
        }

        # Replace the tags with actual data
        for tag, value in replacements.items():
            template_str = template_str.replace(tag, value)
        
        # Return the processed JSON object
        return json.loads(template_str)

class MQTTCommand(models.Model):
    STATE_PENDING = 'pending'
    STATE_SENT = 'sent'
    STATE_NO_RESPONSE = 'no_response'
    STATE_ERROR = 'error'
    STATE_SUCCESS = 'success'

    STATE_CHOICES = [
        (STATE_PENDING, 'Pending'),
        (STATE_SENT, 'Sent'),
        (STATE_NO_RESPONSE, 'No Response'),
        (STATE_ERROR, 'Error'),
        (STATE_SUCCESS, 'Success'),
    ]
    command_id = models.CharField(max_length=255, unique=True)
    command_template = models.ForeignKey(MqttCommandTemplate, on_delete=models.CASCADE, related_name='commands')
    smartreaders = models.ManyToManyField(SmartReader, related_name='mqtt_commands')
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default=STATE_PENDING)
    response = models.JSONField(null=True, blank=True)  # Stores the JSON response from the SmartReader
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    command_id = models.CharField(max_length=255, unique=True, default=uuid.uuid4)

    def send_command(self):
        """
        This method would handle sending the command to the SmartReader.
        It will also update the command's state based on the response.
        """
        self.state = self.STATE_SENT
        self.save()

    def set_error_state(self, error_message):
        self.state = self.STATE_ERROR
        self.response = {"error": error_message}
        self.updated_at = timezone.now()
        self.save()

    def set_success_state(self, response_data):
        self.state = self.STATE_SUCCESS
        self.response = response_data
        self.updated_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f'{self.command_template.name} -> {self.get_command_type_display()} -> {self.smartreaders.first().reader_serial} ({self.state})'

    @property
    def get_command_type_display(self):
        return self.command_template.get_command_type_display()

class MQTTConfiguration(models.Model):
    # General MQTT settings
    enable_mqtt = models.BooleanField(default=False)
    enable_batch_list_reporting = models.BooleanField(default=False)
    clear_batch_list_on_reload = models.BooleanField(default=False)
    publish_batch_list_on_change = models.BooleanField(default=False)
    publish_batch_list_on_change_interval = models.IntegerField(default=10)
    enable_publish_interval_for_batch_lists = models.BooleanField(default=False)
    publish_interval = models.IntegerField(default=60)
    filter_batch_updates_based_on_antenna_zone = models.BooleanField(default=False)
    filter_batch_updates_based_on_antenna_zone_grouping = models.BooleanField(default=False)
    
    # Broker settings
    broker_username = models.CharField(max_length=255, blank=True, null=True)
    broker_password = models.CharField(max_length=255, blank=True, null=True)
    broker_hostname = models.CharField(max_length=255)
    broker_port = models.IntegerField(default=1883)
    mqtt_broker_keepalive = models.IntegerField(default=60)
    mqtt_broker_clean_session = models.BooleanField(default=True)
    mqtt_broker_protocol = models.CharField(
        max_length=3,
        choices=[('tcp', 'TCP'), ('ws', 'Web Socket'), ('wss', 'Secure Web Socket')],
        default='tcp'
    )
    
    # Tag Events Topic
    mqtt_tag_events_topic = models.CharField(max_length=255, default='smartreader/tagEvents')
    mqtt_tag_events_qos_level = models.IntegerField(default=1)
    mqtt_tag_events_retain = models.BooleanField(default=False)
    
    # Management Events Topic
    mqtt_management_events_topic = models.CharField(max_length=255, default='smartreader/managementEvents')
    mqtt_management_events_qos_level = models.IntegerField(default=0)
    mqtt_management_events_retain = models.BooleanField(default=False)
    
    # Metrics Topic
    mqtt_metrics_topic = models.CharField(max_length=255, default='smartreader/metrics')
    mqtt_metrics_qos_level = models.IntegerField(default=0)
    mqtt_metrics_retain = models.BooleanField(default=False)
    
    # Command Topics
    enable_command_receiver = models.BooleanField(default=False)
    
    # Management Command Topics
    mqtt_management_command_topic = models.CharField(max_length=255, blank=True, null=True)
    mqtt_management_command_qos_level = models.IntegerField(default=1)
    mqtt_management_command_response_topic = models.CharField(max_length=255, blank=True, null=True)
    mqtt_management_command_response_qos_level = models.IntegerField(default=0)
    mqtt_management_command_retain = models.BooleanField(default=False)
    
    # Control Command Topics
    mqtt_control_command_topic = models.CharField(max_length=255, blank=True, null=True)
    mqtt_control_command_qos_level = models.IntegerField(default=0)
    mqtt_control_command_response_topic = models.CharField(max_length=255, blank=True, null=True)
    mqtt_control_command_response_qos_level = models.IntegerField(default=0)
    mqtt_control_command_retain = models.BooleanField(default=False)

    def __str__(self):
        return f"MQTT Configuration for {self.broker_hostname}:{self.broker_port}"
    
class StatusEvent(models.Model):
    smartreader = models.ForeignKey(SmartReader, on_delete=models.CASCADE, related_name='status_events')
    reader_name = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    mac_address = models.CharField(max_length=255)
    status = models.CharField(max_length=255)
    component = models.CharField(max_length=255)
    ip_addresses = models.TextField()  # Storing multiple IPs as a semicolon-separated string
    active_preset = models.CharField(max_length=255, null=True, blank=True)
    manufacturer = models.CharField(max_length=255, null=True, blank=True)
    product_hla = models.CharField(max_length=255, null=True, blank=True)
    product_model = models.CharField(max_length=255, null=True, blank=True)
    product_sku = models.CharField(max_length=255, null=True, blank=True)
    product_description = models.TextField(null=True, blank=True)
    is_antenna_hub_enabled = models.BooleanField(default=False)
    reader_operating_region = models.CharField(max_length=255, null=True, blank=True)
    
    # GPI/GPO Information
    gpi1 = models.CharField(max_length=255, null=True, blank=True)
    gpi2 = models.CharField(max_length=255, null=True, blank=True)
    gpo1_admin_status = models.CharField(max_length=255, null=True, blank=True)
    gpo2_admin_status = models.CharField(max_length=255, null=True, blank=True)
    gpo3_admin_status = models.CharField(max_length=255, null=True, blank=True)
    gpo1_operation_status = models.CharField(max_length=255, null=True, blank=True)
    gpo2_operation_status = models.CharField(max_length=255, null=True, blank=True)
    gpo3_operation_status = models.CharField(max_length=255, null=True, blank=True)
    
    # Versions and System Info
    boot_env_version = models.CharField(max_length=255, null=True, blank=True)
    hla_version = models.CharField(max_length=255, null=True, blank=True)
    hardware_version = models.CharField(max_length=255, null=True, blank=True)
    int_hardware_version = models.CharField(max_length=255, null=True, blank=True)
    model_name = models.CharField(max_length=255, null=True, blank=True)
    serial_number = models.CharField(max_length=255, null=True, blank=True)
    int_serial_number = models.CharField(max_length=255, null=True, blank=True)
    features_valid = models.TextField(null=True, blank=True)
    bios_version = models.CharField(max_length=255, null=True, blank=True)
    ptn = models.CharField(max_length=255, null=True, blank=True)
    uptime_seconds = models.IntegerField(null=True, blank=True)
    boot_status = models.CharField(max_length=255, null=True, blank=True)
    boot_reason = models.CharField(max_length=255, null=True, blank=True)
    power_fail_time = models.IntegerField(null=True, blank=True)
    active_power_source = models.CharField(max_length=255, null=True, blank=True)
    total_memory = models.BigIntegerField(null=True, blank=True)
    free_memory = models.BigIntegerField(null=True, blank=True)
    used_memory = models.BigIntegerField(null=True, blank=True)
    cpu_utilization = models.IntegerField(null=True, blank=True)
    total_configuration_storage_space = models.BigIntegerField(null=True, blank=True)
    free_configuration_storage_space = models.BigIntegerField(null=True, blank=True)
    total_application_storage_space = models.BigIntegerField(null=True, blank=True)
    free_application_storage_space = models.BigIntegerField(null=True, blank=True)
    service_enabled = models.BooleanField(default=False)
    negotiation_timeout = models.IntegerField(null=True, blank=True)
    poe_plus_required = models.BooleanField(default=False)
    negotiation_state = models.CharField(max_length=255, null=True, blank=True)
    required_power_available = models.CharField(max_length=255, null=True, blank=True)
    requested_power = models.IntegerField(null=True, blank=True)
    allocated_power = models.IntegerField(null=True, blank=True)
    power_source = models.CharField(max_length=255, null=True, blank=True)
    primary_image_type = models.CharField(max_length=255, null=True, blank=True)
    primary_image_state = models.CharField(max_length=255, null=True, blank=True)
    primary_image_system_version = models.CharField(max_length=255, null=True, blank=True)
    primary_image_config_version = models.CharField(max_length=255, null=True, blank=True)
    primary_image_custom_app_version = models.CharField(max_length=255, null=True, blank=True)
    secondary_image_type = models.CharField(max_length=255, null=True, blank=True)
    secondary_image_state = models.CharField(max_length=255, null=True, blank=True)
    secondary_image_system_version = models.CharField(max_length=255, null=True, blank=True)
    secondary_image_config_version = models.CharField(max_length=255, null=True, blank=True)
    secondary_image_custom_app_version = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f'{self.reader_name} - {self.timestamp}'

class AntennaStatus(models.Model):
    status_event = models.ForeignKey(StatusEvent, on_delete=models.CASCADE, related_name='antenna_status')
    antenna_number = models.PositiveIntegerField()  # 1 to 32
    enabled = models.BooleanField(default=False)
    zone = models.CharField(max_length=255, null=True, blank=True)
    tx_power = models.IntegerField(null=True, blank=True)
    rx_sensitivity = models.IntegerField(null=True, blank=True)
    operational_status = models.CharField(max_length=255, null=True, blank=True)
    last_power_level = models.IntegerField(null=True, blank=True)
    last_noise_level = models.IntegerField(null=True, blank=True)
    energized_time = models.IntegerField(null=True, blank=True)
    unique_inventory_count = models.IntegerField(null=True, blank=True)
    total_inventory_count = models.IntegerField(null=True, blank=True)
    failed_inventory_count = models.IntegerField(null=True, blank=True)
    read_count = models.IntegerField(null=True, blank=True)
    failed_read_count = models.IntegerField(null=True, blank=True)
    write_count = models.IntegerField(null=True, blank=True)
    failed_write_count = models.IntegerField(null=True, blank=True)
    lock_count = models.IntegerField(null=True, blank=True)
    failed_lock_count = models.IntegerField(null=True, blank=True)
    kill_count = models.IntegerField(null=True, blank=True)
    failed_kill_count = models.IntegerField(null=True, blank=True)
    erase_count = models.IntegerField(null=True, blank=True)
    failed_erase_count = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f'{self.status_event.reader_name} - Antenna {self.antenna_number}'

class ConnectionEvent(models.Model):
    smartreader = models.ForeignKey(SmartReader, on_delete=models.CASCADE, related_name='connection_events')
    status = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

class DisconnectionEvent(models.Model):
    smartreader = models.ForeignKey(SmartReader, on_delete=models.CASCADE, related_name='disconnection_events')
    status = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

class InventoryStatusEvent(models.Model):
    smartreader = models.ForeignKey(SmartReader, on_delete=models.CASCADE, related_name='inventory_status_events')
    status = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

class HeartbeatEvent(models.Model):
    smartreader = models.ForeignKey(SmartReader, on_delete=models.CASCADE, related_name='heartbeat_events')
    reader_name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=255)
    tag_reads = models.JSONField()  # Assuming tag_reads is a JSON object

class GPIEvent(models.Model):
    smartreader = models.ForeignKey(SmartReader, on_delete=models.CASCADE, related_name='gpi_events')
    reader_name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=255)
    timestamp = models.DateTimeField()
    gpi1_state = models.CharField(max_length=10)  # Store state of GPI 1, e.g., "high" or "low"
    gpi2_state = models.CharField(max_length=10)  # Store state of GPI 2, e.g., "high" or "low"

    def __str__(self):
        return f'{self.reader_name} - GPI Event at {self.timestamp}'
    

    
