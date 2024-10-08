# Generated by Django 4.2.15 on 2024-09-02 19:06

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Condition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field', models.CharField(max_length=255)),
                ('value', models.CharField(max_length=255)),
                ('comparison_type', models.CharField(blank=True, choices=[('remains_same', 'Remains the Same'), ('greater_than', 'Greater Than'), ('lower_than', 'Lower Than')], max_length=50, null=True)),
                ('compare_with_previous', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='MqttCommandTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('template_content', models.JSONField(default=dict)),
                ('command_type', models.CharField(choices=[('control', 'Control'), ('management', 'Management')], max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='MQTTConfiguration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('enable_mqtt', models.BooleanField(default=False)),
                ('enable_batch_list_reporting', models.BooleanField(default=False)),
                ('clear_batch_list_on_reload', models.BooleanField(default=False)),
                ('publish_batch_list_on_change', models.BooleanField(default=False)),
                ('publish_batch_list_on_change_interval', models.IntegerField(default=10)),
                ('enable_publish_interval_for_batch_lists', models.BooleanField(default=False)),
                ('publish_interval', models.IntegerField(default=60)),
                ('filter_batch_updates_based_on_antenna_zone', models.BooleanField(default=False)),
                ('filter_batch_updates_based_on_antenna_zone_grouping', models.BooleanField(default=False)),
                ('broker_username', models.CharField(blank=True, max_length=255, null=True)),
                ('broker_password', models.CharField(blank=True, max_length=255, null=True)),
                ('broker_hostname', models.CharField(max_length=255)),
                ('broker_port', models.IntegerField(default=1883)),
                ('mqtt_broker_keepalive', models.IntegerField(default=60)),
                ('mqtt_broker_clean_session', models.BooleanField(default=True)),
                ('mqtt_broker_protocol', models.CharField(choices=[('tcp', 'TCP'), ('ws', 'Web Socket'), ('wss', 'Secure Web Socket')], default='tcp', max_length=3)),
                ('mqtt_tag_events_topic', models.CharField(default='smartreader/tagEvents', max_length=255)),
                ('mqtt_tag_events_qos_level', models.IntegerField(default=1)),
                ('mqtt_tag_events_retain', models.BooleanField(default=False)),
                ('mqtt_management_events_topic', models.CharField(default='smartreader/managementEvents', max_length=255)),
                ('mqtt_management_events_qos_level', models.IntegerField(default=0)),
                ('mqtt_management_events_retain', models.BooleanField(default=False)),
                ('mqtt_metrics_topic', models.CharField(default='smartreader/metrics', max_length=255)),
                ('mqtt_metrics_qos_level', models.IntegerField(default=0)),
                ('mqtt_metrics_retain', models.BooleanField(default=False)),
                ('enable_command_receiver', models.BooleanField(default=False)),
                ('mqtt_management_command_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_management_command_qos_level', models.IntegerField(default=1)),
                ('mqtt_management_command_response_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_management_command_response_qos_level', models.IntegerField(default=0)),
                ('mqtt_management_command_retain', models.BooleanField(default=False)),
                ('mqtt_control_command_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_control_command_qos_level', models.IntegerField(default=0)),
                ('mqtt_control_command_response_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_control_command_response_qos_level', models.IntegerField(default=0)),
                ('mqtt_control_command_retain', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='SmartReader',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reader_name', models.CharField(max_length=255)),
                ('reader_serial', models.CharField(max_length=255)),
                ('is_enabled', models.BooleanField(default=False)),
                ('license_key', models.CharField(max_length=255)),
                ('profile_name', models.CharField(max_length=255)),
                ('is_current_profile', models.BooleanField(default=False)),
                ('antenna_ports', models.CharField(default='1,2,3,4', max_length=255)),
                ('antenna_states', models.CharField(default='1,0,0,0', max_length=255)),
                ('antenna_zones', models.CharField(default='antenna,antenna,antenna,antenna', max_length=255)),
                ('transmit_power', models.CharField(default='1500,1500,1500,1500', max_length=255)),
                ('receive_sensitivity', models.CharField(default='-92,-92,-92,-92', max_length=255)),
                ('reader_mode', models.IntegerField(default=3)),
                ('search_mode', models.IntegerField(default=1)),
                ('session', models.IntegerField(default=1)),
                ('tag_population', models.IntegerField(default=32)),
                ('start_trigger_type', models.IntegerField(default=1)),
                ('start_trigger_period', models.IntegerField(default=0)),
                ('start_trigger_offset', models.IntegerField(default=0)),
                ('start_trigger_utc_timestamp', models.IntegerField(default=0)),
                ('start_trigger_gpi_event', models.IntegerField(default=1)),
                ('start_trigger_gpi_port', models.IntegerField(default=1)),
                ('stop_trigger_type', models.IntegerField(default=0)),
                ('stop_trigger_duration', models.IntegerField(default=0)),
                ('stop_trigger_timeout', models.IntegerField(default=0)),
                ('stop_trigger_gpi_event', models.IntegerField(default=0)),
                ('stop_trigger_gpi_port', models.IntegerField(default=1)),
                ('socket_server', models.BooleanField(default=False)),
                ('socket_port', models.IntegerField(default=14150)),
                ('socket_command_server', models.BooleanField(default=False)),
                ('socket_command_server_port', models.IntegerField(default=14151)),
                ('udp_server', models.BooleanField(default=False)),
                ('udp_ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('udp_reader_port', models.IntegerField(blank=True, default=11000, null=True)),
                ('udp_remote_ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('udp_remote_port', models.IntegerField(blank=True, default=10000, null=True)),
                ('http_post_enabled', models.BooleanField(default=False)),
                ('http_post_type', models.IntegerField(default=1)),
                ('http_post_interval_sec', models.IntegerField(default=5)),
                ('http_post_url', models.URLField(default='http://server:8000/webhook/', max_length=2048)),
                ('http_authentication_type', models.CharField(blank=True, default='NONE', max_length=50, null=True)),
                ('http_authentication_username', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('http_authentication_password', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('http_authentication_token_api_enabled', models.BooleanField(default=False)),
                ('http_authentication_token_api_url', models.URLField(blank=True, default='', max_length=2048, null=True)),
                ('http_authentication_token_api_body', models.TextField(blank=True, default='', null=True)),
                ('http_authentication_token_api_value', models.TextField(blank=True, default='', null=True)),
                ('http_authentication_header', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('http_authentication_header_value', models.CharField(blank=True, default='', max_length=255, null=True)),
                ('http_verify_post_http_return_code', models.BooleanField(default=False)),
                ('mqtt_enabled', models.BooleanField(default=False)),
                ('mqtt_use_ssl', models.BooleanField(default=False)),
                ('mqtt_ssl_ca_certificate', models.TextField(blank=True, null=True)),
                ('mqtt_ssl_client_certificate', models.TextField(blank=True, null=True)),
                ('mqtt_ssl_client_certificate_password', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_broker_name', models.CharField(blank=True, default='MQTT-SERVER', max_length=255, null=True)),
                ('mqtt_broker_address', models.GenericIPAddressField(blank=True, null=True)),
                ('mqtt_broker_port', models.IntegerField(blank=True, default=1883, null=True)),
                ('mqtt_broker_clean_session', models.BooleanField(default=True)),
                ('mqtt_broker_keep_alive', models.IntegerField(blank=True, null=True)),
                ('mqtt_broker_debug', models.BooleanField(default=False)),
                ('mqtt_tag_events_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_tag_events_qos', models.IntegerField(blank=True, null=True)),
                ('mqtt_tag_events_retain_messages', models.BooleanField(default=False)),
                ('mqtt_management_events_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_management_events_qos', models.IntegerField(blank=True, null=True)),
                ('mqtt_management_events_retain_messages', models.BooleanField(default=False)),
                ('mqtt_metric_events_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_metric_events_qos', models.IntegerField(blank=True, null=True)),
                ('mqtt_metric_events_retain_messages', models.BooleanField(default=False)),
                ('mqtt_management_command_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_management_command_qos', models.IntegerField(blank=True, null=True)),
                ('mqtt_management_command_retain_messages', models.BooleanField(default=False)),
                ('mqtt_management_response_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_management_response_qos', models.IntegerField(blank=True, null=True)),
                ('mqtt_management_response_retain_messages', models.BooleanField(default=False)),
                ('mqtt_control_command_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_control_command_qos', models.IntegerField(blank=True, null=True)),
                ('mqtt_control_command_retain_messages', models.BooleanField(default=False)),
                ('mqtt_control_response_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_control_response_qos', models.IntegerField(blank=True, null=True)),
                ('mqtt_control_response_retain_messages', models.BooleanField(default=False)),
                ('mqtt_lwt_topic', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_lwt_qos', models.IntegerField(blank=True, null=True)),
                ('mqtt_username', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_password', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_proxy_url', models.URLField(blank=True, max_length=2048, null=True)),
                ('mqtt_proxy_username', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_proxy_password', models.CharField(blank=True, max_length=255, null=True)),
                ('mqtt_publish_interval_sec', models.IntegerField(blank=True, null=True)),
                ('mqtt_enable_smartreader_default_topics', models.BooleanField(default=False)),
                ('is_cloud_interface', models.BooleanField(default=False)),
                ('apply_ip_settings_on_startup', models.BooleanField(default=False)),
                ('ip_address_mode', models.CharField(blank=True, max_length=50, null=True)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('ip_mask', models.GenericIPAddressField(blank=True, null=True)),
                ('gateway_address', models.GenericIPAddressField(blank=True, null=True)),
                ('broadcast_address', models.GenericIPAddressField(blank=True, null=True)),
                ('software_filter_enabled', models.BooleanField(default=False)),
                ('software_filter_window_sec', models.IntegerField(blank=True, null=True)),
                ('software_filter_field', models.IntegerField(blank=True, null=True)),
                ('software_filter_read_count_timeout_enabled', models.BooleanField(default=False)),
                ('software_filter_read_count_timeout_seen_count', models.IntegerField(blank=True, null=True)),
                ('software_filter_read_count_timeout_interval_in_sec', models.IntegerField(blank=True, null=True)),
                ('include_reader_name', models.BooleanField(default=True)),
                ('include_antenna_port', models.BooleanField(default=True)),
                ('include_antenna_zone', models.BooleanField(default=False)),
                ('include_first_seen_timestamp', models.BooleanField(default=True)),
                ('include_peak_rssi', models.BooleanField(default=False)),
                ('include_rf_phase_angle', models.BooleanField(default=False)),
                ('include_rf_doppler_frequency', models.BooleanField(default=False)),
                ('include_rf_channel_index', models.BooleanField(default=False)),
                ('include_gpi_event', models.BooleanField(default=False)),
                ('include_inventory_status_event', models.BooleanField(default=False)),
                ('include_inventory_status_event_id', models.IntegerField(blank=True, null=True)),
                ('include_inventory_status_event_total_count', models.IntegerField(blank=True, null=True)),
                ('include_tid', models.BooleanField(default=False)),
                ('tid_word_start', models.IntegerField(blank=True, null=True)),
                ('tid_word_count', models.IntegerField(blank=True, null=True)),
                ('include_user_memory', models.BooleanField(default=False)),
                ('user_memory_word_start', models.IntegerField(blank=True, null=True)),
                ('user_memory_word_count', models.IntegerField(blank=True, null=True)),
                ('heartbeat_enabled', models.BooleanField(default=False)),
                ('heartbeat_period_sec', models.IntegerField(blank=True, null=True)),
                ('heartbeat_url', models.URLField(blank=True, max_length=2048, null=True)),
                ('heartbeat_http_authentication_type', models.CharField(blank=True, max_length=50, null=True)),
                ('heartbeat_http_authentication_username', models.CharField(blank=True, max_length=255, null=True)),
                ('heartbeat_http_authentication_password', models.CharField(blank=True, max_length=255, null=True)),
                ('heartbeat_http_authentication_token_api_enabled', models.BooleanField(default=False)),
                ('heartbeat_http_authentication_token_api_url', models.URLField(blank=True, max_length=2048, null=True)),
                ('heartbeat_http_authentication_token_api_body', models.TextField(blank=True, null=True)),
                ('heartbeat_http_authentication_token_api_username_field', models.CharField(blank=True, max_length=255, null=True)),
                ('heartbeat_http_authentication_token_api_username_value', models.CharField(blank=True, max_length=255, null=True)),
                ('heartbeat_http_authentication_token_api_password_field', models.CharField(blank=True, max_length=255, null=True)),
                ('heartbeat_http_authentication_token_api_password_value', models.CharField(blank=True, max_length=255, null=True)),
                ('heartbeat_http_authentication_token_api_value', models.TextField(blank=True, null=True)),
                ('custom_field_1_enabled', models.BooleanField(default=False)),
                ('custom_field_1_name', models.CharField(blank=True, max_length=255, null=True)),
                ('custom_field_1_value', models.CharField(blank=True, max_length=255, null=True)),
                ('custom_field_2_enabled', models.BooleanField(default=False)),
                ('custom_field_2_name', models.CharField(blank=True, max_length=255, null=True)),
                ('custom_field_2_value', models.CharField(blank=True, max_length=255, null=True)),
                ('custom_field_3_enabled', models.BooleanField(default=False)),
                ('custom_field_3_name', models.CharField(blank=True, max_length=255, null=True)),
                ('custom_field_3_value', models.CharField(blank=True, max_length=255, null=True)),
                ('custom_field_4_enabled', models.BooleanField(default=False)),
                ('custom_field_4_name', models.CharField(blank=True, max_length=255, null=True)),
                ('custom_field_4_value', models.CharField(blank=True, max_length=255, null=True)),
                ('is_log_file_enabled', models.BooleanField(default=False)),
                ('operating_region', models.CharField(blank=True, max_length=255, null=True)),
                ('system_image_upgrade_url', models.URLField(blank=True, max_length=2048, null=True)),
                ('system_disable_image_fallback_status', models.BooleanField(default=False)),
                ('smartreader_enabled_for_management_only', models.BooleanField(default=False)),
                ('status', models.CharField(blank=True, max_length=255, null=True)),
                ('field_delim', models.CharField(blank=True, max_length=10, null=True)),
                ('advanced_gpo_mode_3', models.CharField(blank=True, max_length=255, null=True)),
                ('c1g2_filter_bank', models.IntegerField(blank=True, null=True)),
                ('data_suffix', models.CharField(blank=True, max_length=255, null=True)),
                ('field_ping_interval', models.IntegerField(blank=True, null=True)),
                ('backup_to_internal_flash_enabled', models.BooleanField(default=False)),
                ('c1g2_filter_enabled', models.BooleanField(default=False)),
                ('empty_field_timeout', models.IntegerField(blank=True, null=True)),
                ('advanced_gpo_mode_2', models.CharField(blank=True, max_length=255, null=True)),
                ('keep_filename_on_day_change', models.BooleanField(default=False)),
                ('prompt_before_changing', models.BooleanField(default=False)),
                ('tag_validation_enabled', models.BooleanField(default=False)),
                ('advanced_gpo_enabled', models.BooleanField(default=False)),
                ('site_enabled', models.BooleanField(default=False)),
                ('usb_flash_drive', models.CharField(blank=True, max_length=255, null=True)),
                ('c1g2_filter_mask', models.CharField(blank=True, max_length=255, null=True)),
                ('connection_status', models.CharField(blank=True, max_length=255, null=True)),
                ('site', models.CharField(blank=True, max_length=255, null=True)),
                ('truncate_start', models.IntegerField(blank=True, null=True)),
                ('advanced_gpo_mode_1', models.CharField(blank=True, max_length=255, null=True)),
                ('c1g2_filter_len', models.IntegerField(blank=True, null=True)),
                ('c1g2_filter_pointer', models.IntegerField(blank=True, null=True)),
                ('backup_to_flash_drive_on_gpi_event_enabled', models.BooleanField(default=False)),
                ('truncate_epc', models.BooleanField(default=False)),
                ('usb_hid', models.BooleanField(default=False)),
                ('baud_rate', models.IntegerField(blank=True, null=True)),
                ('max_tx_power_on_gpi_event_enabled', models.BooleanField(default=False)),
                ('serial_port', models.CharField(blank=True, max_length=255, null=True)),
                ('low_duty_cycle_enabled', models.BooleanField(default=False)),
                ('line_end', models.CharField(blank=True, max_length=10, null=True)),
                ('data_prefix', models.CharField(blank=True, max_length=255, null=True)),
                ('truncate_len', models.IntegerField(blank=True, null=True)),
                ('c1g2_filter_match_option', models.CharField(blank=True, max_length=255, null=True)),
                ('advanced_gpo_mode_4', models.CharField(blank=True, max_length=255, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='StatusEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reader_name', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField()),
                ('mac_address', models.CharField(max_length=255)),
                ('status', models.CharField(max_length=255)),
                ('component', models.CharField(max_length=255)),
                ('ip_addresses', models.TextField()),
                ('active_preset', models.CharField(blank=True, max_length=255, null=True)),
                ('manufacturer', models.CharField(blank=True, max_length=255, null=True)),
                ('product_hla', models.CharField(blank=True, max_length=255, null=True)),
                ('product_model', models.CharField(blank=True, max_length=255, null=True)),
                ('product_sku', models.CharField(blank=True, max_length=255, null=True)),
                ('product_description', models.TextField(blank=True, null=True)),
                ('is_antenna_hub_enabled', models.BooleanField(default=False)),
                ('reader_operating_region', models.CharField(blank=True, max_length=255, null=True)),
                ('gpi1', models.CharField(blank=True, max_length=255, null=True)),
                ('gpi2', models.CharField(blank=True, max_length=255, null=True)),
                ('gpo1_admin_status', models.CharField(blank=True, max_length=255, null=True)),
                ('gpo2_admin_status', models.CharField(blank=True, max_length=255, null=True)),
                ('gpo3_admin_status', models.CharField(blank=True, max_length=255, null=True)),
                ('gpo1_operation_status', models.CharField(blank=True, max_length=255, null=True)),
                ('gpo2_operation_status', models.CharField(blank=True, max_length=255, null=True)),
                ('gpo3_operation_status', models.CharField(blank=True, max_length=255, null=True)),
                ('boot_env_version', models.CharField(blank=True, max_length=255, null=True)),
                ('hla_version', models.CharField(blank=True, max_length=255, null=True)),
                ('hardware_version', models.CharField(blank=True, max_length=255, null=True)),
                ('int_hardware_version', models.CharField(blank=True, max_length=255, null=True)),
                ('model_name', models.CharField(blank=True, max_length=255, null=True)),
                ('serial_number', models.CharField(blank=True, max_length=255, null=True)),
                ('int_serial_number', models.CharField(blank=True, max_length=255, null=True)),
                ('features_valid', models.TextField(blank=True, null=True)),
                ('bios_version', models.CharField(blank=True, max_length=255, null=True)),
                ('ptn', models.CharField(blank=True, max_length=255, null=True)),
                ('uptime_seconds', models.IntegerField(blank=True, null=True)),
                ('boot_status', models.CharField(blank=True, max_length=255, null=True)),
                ('boot_reason', models.CharField(blank=True, max_length=255, null=True)),
                ('power_fail_time', models.IntegerField(blank=True, null=True)),
                ('active_power_source', models.CharField(blank=True, max_length=255, null=True)),
                ('total_memory', models.BigIntegerField(blank=True, null=True)),
                ('free_memory', models.BigIntegerField(blank=True, null=True)),
                ('used_memory', models.BigIntegerField(blank=True, null=True)),
                ('cpu_utilization', models.IntegerField(blank=True, null=True)),
                ('total_configuration_storage_space', models.BigIntegerField(blank=True, null=True)),
                ('free_configuration_storage_space', models.BigIntegerField(blank=True, null=True)),
                ('total_application_storage_space', models.BigIntegerField(blank=True, null=True)),
                ('free_application_storage_space', models.BigIntegerField(blank=True, null=True)),
                ('service_enabled', models.BooleanField(default=False)),
                ('negotiation_timeout', models.IntegerField(blank=True, null=True)),
                ('poe_plus_required', models.BooleanField(default=False)),
                ('negotiation_state', models.CharField(blank=True, max_length=255, null=True)),
                ('required_power_available', models.CharField(blank=True, max_length=255, null=True)),
                ('requested_power', models.IntegerField(blank=True, null=True)),
                ('allocated_power', models.IntegerField(blank=True, null=True)),
                ('power_source', models.CharField(blank=True, max_length=255, null=True)),
                ('primary_image_type', models.CharField(blank=True, max_length=255, null=True)),
                ('primary_image_state', models.CharField(blank=True, max_length=255, null=True)),
                ('primary_image_system_version', models.CharField(blank=True, max_length=255, null=True)),
                ('primary_image_config_version', models.CharField(blank=True, max_length=255, null=True)),
                ('primary_image_custom_app_version', models.CharField(blank=True, max_length=255, null=True)),
                ('secondary_image_type', models.CharField(blank=True, max_length=255, null=True)),
                ('secondary_image_state', models.CharField(blank=True, max_length=255, null=True)),
                ('secondary_image_system_version', models.CharField(blank=True, max_length=255, null=True)),
                ('secondary_image_config_version', models.CharField(blank=True, max_length=255, null=True)),
                ('secondary_image_custom_app_version', models.CharField(blank=True, max_length=255, null=True)),
                ('smartreader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_events', to='smartreader.smartreader')),
            ],
        ),
        migrations.CreateModel(
            name='MQTTCommand',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('no_response', 'No Response'), ('error', 'Error'), ('success', 'Success')], default='pending', max_length=20)),
                ('response', models.JSONField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('command_id', models.CharField(default=uuid.uuid4, max_length=255, unique=True)),
                ('command_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='commands', to='smartreader.mqttcommandtemplate')),
                ('smartreaders', models.ManyToManyField(related_name='mqtt_commands', to='smartreader.smartreader')),
            ],
        ),
        migrations.CreateModel(
            name='InventoryStatusEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('smartreader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_status_events', to='smartreader.smartreader')),
            ],
        ),
        migrations.CreateModel(
            name='HeartbeatEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reader_name', models.CharField(max_length=255)),
                ('mac_address', models.CharField(max_length=255)),
                ('tag_reads', models.JSONField()),
                ('smartreader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='heartbeat_events', to='smartreader.smartreader')),
            ],
        ),
        migrations.CreateModel(
            name='GPIEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reader_name', models.CharField(max_length=255)),
                ('mac_address', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField()),
                ('gpi1_state', models.CharField(max_length=10)),
                ('gpi2_state', models.CharField(max_length=10)),
                ('smartreader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gpi_events', to='smartreader.smartreader')),
            ],
        ),
        migrations.CreateModel(
            name='DisconnectionEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('smartreader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='disconnection_events', to='smartreader.smartreader')),
            ],
        ),
        migrations.CreateModel(
            name='ConnectionEvent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(max_length=255)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('smartreader', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='connection_events', to='smartreader.smartreader')),
            ],
        ),
        migrations.CreateModel(
            name='AntennaStatus',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('antenna_number', models.PositiveIntegerField()),
                ('enabled', models.BooleanField(default=False)),
                ('zone', models.CharField(blank=True, max_length=255, null=True)),
                ('tx_power', models.IntegerField(blank=True, null=True)),
                ('rx_sensitivity', models.IntegerField(blank=True, null=True)),
                ('operational_status', models.CharField(blank=True, max_length=255, null=True)),
                ('last_power_level', models.IntegerField(blank=True, null=True)),
                ('last_noise_level', models.IntegerField(blank=True, null=True)),
                ('energized_time', models.IntegerField(blank=True, null=True)),
                ('unique_inventory_count', models.IntegerField(blank=True, null=True)),
                ('total_inventory_count', models.IntegerField(blank=True, null=True)),
                ('failed_inventory_count', models.IntegerField(blank=True, null=True)),
                ('read_count', models.IntegerField(blank=True, null=True)),
                ('failed_read_count', models.IntegerField(blank=True, null=True)),
                ('write_count', models.IntegerField(blank=True, null=True)),
                ('failed_write_count', models.IntegerField(blank=True, null=True)),
                ('lock_count', models.IntegerField(blank=True, null=True)),
                ('failed_lock_count', models.IntegerField(blank=True, null=True)),
                ('kill_count', models.IntegerField(blank=True, null=True)),
                ('failed_kill_count', models.IntegerField(blank=True, null=True)),
                ('erase_count', models.IntegerField(blank=True, null=True)),
                ('failed_erase_count', models.IntegerField(blank=True, null=True)),
                ('status_event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='antenna_status', to='smartreader.statusevent')),
            ],
        ),
        migrations.CreateModel(
            name='AlertRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('active', models.BooleanField(default=True)),
                ('last_triggered', models.DateTimeField(blank=True, null=True)),
                ('trigger_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('smartreaders', models.ManyToManyField(related_name='alert_rules', to='smartreader.smartreader')),
            ],
        ),
        migrations.CreateModel(
            name='AlertCondition',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('event_type', models.CharField(max_length=255)),
                ('field_name', models.CharField(max_length=255)),
                ('operator', models.CharField(max_length=10)),
                ('comparison_type', models.CharField(choices=[('equals', 'Equals'), ('greater_than', 'Greater Than'), ('less_than', 'Less Than'), ('remains_same', 'Remains the Same')], max_length=50)),
                ('threshold', models.CharField(max_length=255)),
                ('recurrence', models.IntegerField(blank=True, null=True)),
                ('alert_rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conditions', to='smartreader.alertrule')),
            ],
        ),
        migrations.CreateModel(
            name='AlertAction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action_type', models.CharField(choices=[('mqtt', 'MQTT'), ('webhook', 'Webhook')], max_length=50)),
                ('action_value', models.CharField(max_length=255)),
                ('parameters', models.CharField(blank=True, max_length=1024, null=True)),
                ('message_template', models.TextField(blank=True, null=True)),
                ('order', models.IntegerField(default=0)),
                ('alert_rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='actions', to='smartreader.alertrule')),
            ],
        ),
        migrations.CreateModel(
            name='Alert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('triggered_at', models.DateTimeField(auto_now_add=True)),
                ('event_data', models.JSONField()),
                ('resolved', models.BooleanField(default=False)),
                ('alert_rule', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='alerts', to='smartreader.alertrule')),
                ('conditions', models.ManyToManyField(to='smartreader.condition')),
            ],
        ),
    ]
