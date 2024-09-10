from django import forms
from django.forms import modelformset_factory
from .models import AlertRule, AlertCondition, AlertAction, MQTTCommand, MQTTConfiguration, MqttCommandTemplate, SmartReader

class AlertRuleForm(forms.ModelForm):
    class Meta:
        model = AlertRule
        fields = ['name', 'description', 'smartreaders', 'active']  # Exclude fields like 'created_by', 'last_triggered', and 'trigger_count'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'smartreaders': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['smartreaders'].queryset = SmartReader.objects.filter(created_by=user)

    def save(self, commit=True):
        alert_rule = super().save(commit=False)
        if not self.instance.pk:
            # New object, set the created_by field
            alert_rule.created_by = self.initial['user']
        if commit:
            alert_rule.save()
            self.save_m2m()
        return alert_rule

BasicInfoForm = modelformset_factory(
    AlertRule,
    form=AlertRuleForm,
    extra=1,  # Number of extra forms to display
    can_delete=True  # Allow deleting existing conditions
)

class AlertConditionFilterForm(forms.Form):
    condition_type = forms.ChoiceField(
        choices=[('', 'All')] + AlertCondition.CONDITION_TYPES,
        required=False,
        label='Condition Type'
    )
    field_name = forms.CharField(max_length=255, required=False, label='Field Name')
    threshold = forms.CharField(max_length=255, required=False, label='Threshold')
    compare_with_previous = forms.BooleanField(
        required=False, 
        label="Compare with Previous Event"
    )
    comparison_type = forms.ChoiceField(
        choices=[('', '---')] + AlertCondition.COMPARISON_TYPES,
        required=False,
        label="Comparison Type"
    )
    class Meta:
        model = AlertCondition
        fields = ['alert_rule', 'condition_type', 'field_name', 'operator', 'threshold', 'compare_with_previous', 'comparison_type']

    def clean(self):
        cleaned_data = super().clean()
        compare_with_previous = cleaned_data.get('compare_with_previous')
        comparison_type = cleaned_data.get('comparison_type')

        if compare_with_previous and not comparison_type:
            self.add_error('comparison_type', 'Please select a comparison type if you are comparing with the previous event.')

        return cleaned_data

class AlertConditionForm(forms.ModelForm):
    class Meta:
        model = AlertCondition
        fields = ['event_type', 'field_name', 'operator', 'threshold']
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'field_name': forms.Select(attrs={'class': 'form-control'}),
            'operator': forms.Select(attrs={'class': 'form-control'}),
            'threshold': forms.TextInput(attrs={'class': 'form-control'}),
        }

ConditionFormSet = modelformset_factory(
    AlertCondition,
    form=AlertConditionForm,
    extra=1,  # Number of extra forms to display
    can_delete=True  # Allow deleting existing conditions
)

class AlertActionForm(forms.ModelForm):
    class Meta:
        model = AlertAction
        fields = ['action_type', 'action_value', 'parameters', 'message_template', 'order']

    def clean(self):
        cleaned_data = super().clean()
        action_type = cleaned_data.get('action_type')

        # Additional validation for specific action types
        if action_type == 'mqtt' and not cleaned_data.get('action_value'):
            self.add_error('action_value', 'MQTT topic is required for MQTT actions.')

        if action_type == 'webhook' and not cleaned_data.get('action_value'):
            self.add_error('action_value', 'Webhook URL is required for Webhook actions.')

        return cleaned_data

ActionFormSet = modelformset_factory(
    AlertAction,
    form=AlertActionForm,
    extra=1,  # Number of extra forms to display
    can_delete=True  # Allow deleting existing conditions
)

class AlertRuleFilterForm(forms.Form):
    name = forms.CharField(
        required=False,
        label='Rule Name',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Search by name'})
    )
    
    STATUS_CHOICES = [
        ('', 'All'),  # For not filtering by status
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]

    status = forms.ChoiceField(
        required=False,
        choices=STATUS_CHOICES,
        label='Status',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

class SmartReaderForm(forms.ModelForm):
    class Meta:
        model = SmartReader
        fields = '__all__'  # Include all fields from the model

    # Customizing the form fields with widgets and placeholders
    advanced_gpo_enabled = forms.BooleanField(
        label='Advanced GPO',
        required=False,
        widget=forms.CheckboxInput()
    )
    advanced_gpo_mode_1 = forms.ChoiceField(
        choices=SmartReader.ADVANCED_GPO_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select'}),
        label='Advanced GPO Modes'
    )
    advanced_gpo_mode_2 = forms.ChoiceField(
        choices=SmartReader.ADVANCED_GPO_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select'}),
        label='Advanced GPO Modes'
    )
    advanced_gpo_mode_3 = forms.ChoiceField(
        choices=SmartReader.ADVANCED_GPO_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select'}),
        label='Advanced GPO Modes'
    )
    antenna_identifier = forms.CharField(
        label='Antenna Identifier',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Antenna Identifier'})
    )
    antenna_ports = forms.CharField(
        label='Antenna Ports',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Antenna Ports'})
    )
    antenna_states = forms.CharField(
        label='Antenna States',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Antenna States'})
    )
    antenna_zones = forms.CharField(
        label='Antenna Zones',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Antenna Zones'})
    )
    apply_ip_settings_on_startup = forms.BooleanField(
        label='Apply IP Settings on Startup',
        required=False,
        widget=forms.CheckboxInput()
    )
    backup_to_flash_drive_on_gpi_event_enabled = forms.BooleanField(
        label='Backup to Flash Drive on GPI Event',
        required=False,
        widget=forms.CheckboxInput()
    )
    backup_to_internal_flash_enabled = forms.BooleanField(
        label='Backup to Internal Flash',
        required=False,
        widget=forms.CheckboxInput()
    )
    barcode_enable_queue = forms.BooleanField(
        label='Enable Barcode Queue',
        required=False,
        widget=forms.CheckboxInput()
    )
    barcode_process_no_data_string = forms.BooleanField(
        label='Process No Data String',
        required=False,
        widget=forms.CheckboxInput()
    )
    barcode_no_data_string = forms.CharField(
        label='Barcode No Data String',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Barcode No Data String'})
    )
    barcode_line_end = forms.CharField(
        label='Barcode Line End',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Barcode Line End'})
    )
    barcode_tcp_address = forms.CharField(
        label='Barcode TCP Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Barcode TCP Address'})
    )
    barcode_tcp_port = forms.IntegerField(
        label='Barcode TCP Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Barcode TCP Port'})
    )
    barcode_tcp_len = forms.IntegerField(
        label='Barcode TCP Length',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Barcode TCP Length'})
    )
    barcode_tcp_no_data_string = forms.CharField(
        label='Barcode TCP No Data String',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Barcode TCP No Data String'})
    )
    baud_rate = forms.IntegerField(
        label='Barcode TCP No Data String',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Baud Rate'})
    )   
    c1g2_filter_enabled = forms.BooleanField(
        label='Enable C1G2 Filter',
        required=False,
        widget=forms.CheckboxInput()
    )
    c1g2_filter_bank = forms.ChoiceField(
        choices=SmartReader.C1G2_BANK_FILTER_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Memory Bank'}),
        label='C1G2 Memory Bank Filter'
    )
    c1g2_filter_len = forms.IntegerField(
        label='C1G2 Filter Len',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter C1G2 Filter Len'})
    )
    c1g2_filter_mask = forms.CharField(
        label='C1G2 Filter Mask',
        widget=forms.TextInput(attrs={'placeholder': 'Enter C1G2 Filter Mask'})
    )
    c1g2_filter_match_option = forms.CharField(
        label='C1G2 Filter Match Option',
        widget=forms.TextInput(attrs={'placeholder': 'Enter C1G2 Match Option'})
    )
    c1g2_filter_pointer = forms.CharField(
        label='C1G2 Filter Pointer',
        widget=forms.TextInput(attrs={'placeholder': 'Enter C1G2 Filter Pointer'})
    )
    cleanup_tag_events_list_batch_on_reload = forms.BooleanField(
        label='Cleanup Tag Events List Batch on Reload',
        required=False,
        widget=forms.CheckboxInput()
    )
    connection_status = forms.BooleanField(
        label='Connection Status',
        required=False,
        widget=forms.CheckboxInput()
    )
    csv_file_format = forms.IntegerField(
        label='CSV File Format',
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter CSV File Format'})
    )
    custom_field_1_enabled = forms.BooleanField(
        label='Custom Field 1 Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    custom_field_1_name = forms.CharField(
        label='Custom Field 1 Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Custom Field 1 Name'})
    )
    custom_field_1_value = forms.CharField(
        label='Custom Field 1 Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Custom Field 1 Value'})
    )
    custom_field_2_enabled = forms.BooleanField(
        label='Custom Field 2 Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    custom_field_2_name = forms.CharField(
        label='Custom Field 2 Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Custom Field 2 Name'})
    )
    custom_field_2_value = forms.CharField(
        label='Custom Field 2 Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Custom Field 2 Value'})
    )
    custom_field_3_enabled = forms.BooleanField(
        label='Custom Field 3 Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    custom_field_3_name = forms.CharField(
        label='Custom Field 3 Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Custom Field 3 Name'})
    )
    custom_field_3_value = forms.CharField(
        label='Custom Field 3 Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Custom Field 3 Value'})
    )
    custom_field_4_enabled = forms.BooleanField(
        label='Custom Field 4 Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    custom_field_4_name = forms.CharField(
        label='Custom Field 4 Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Custom Field 4 Name'})
    )
    custom_field_4_value = forms.CharField(
        label='Custom Field 4 Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Custom Field 4 Value'})
    )
    status = forms.ChoiceField(
        choices=SmartReader.STATUS_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Status'}),
        label='Reader Status'
    )
    reader_name = forms.CharField(
        label='Reader Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Reader Name'})
    )
    reader_serial = forms.CharField(
        label='Reader Serial',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Reader Serial'})
    )
    is_enabled = forms.BooleanField(
        label='Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    license_key = forms.CharField(
        label='License Key',
        widget=forms.TextInput(attrs={'placeholder': 'Enter License Key'})
    )
    profile_name = forms.CharField(
        label='Profile Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Profile Name'})
    )
    is_current_profile = forms.BooleanField(
        label='Current Profile',
        required=False,
        widget=forms.CheckboxInput()
    )
    transmit_power = forms.CharField(
        label='Transmit Power',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Transmit Power'})
    )
    receive_sensitivity = forms.CharField(
        label='Receive Sensitivity',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Receive Sensitivity'})
    )
    reader_mode = forms.ChoiceField(
        label='Reader Mode',
        choices=SmartReader.READER_MODE_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Reader Mode'})
    )
    search_mode = forms.ChoiceField(
        label='Search Mode',
        choices=SmartReader.SEARCH_MODE_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Search Mode'})
    )
    session = forms.IntegerField(
        label='Session',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Session'})
    )
    tag_population = forms.IntegerField(
        label='Tag Population',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Tag Population'})
    )
    start_trigger_type = forms.ChoiceField(
        label='Start Trigger Type',
        choices=SmartReader.START_TRIGGER_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Start Trigger Type'})
    )
    start_trigger_period = forms.IntegerField(
        label='Start Trigger Period',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Start Trigger Period'})
    )
    start_trigger_offset = forms.IntegerField(
        label='Start Trigger Offset',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Start Trigger Offset'})
    )
    start_trigger_utc_timestamp = forms.IntegerField(
        label='Start Trigger UTC Timestamp',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Start Trigger UTC Timestamp'})
    )
    start_trigger_gpi_port = forms.ChoiceField(
        label='Start Trigger GPI Port',
        choices=SmartReader.START_TRIGGER_GPI_PORT_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Start Trigger GPI Port'})
    )
    start_trigger_gpi_event = forms.ChoiceField(
        label='Start Trigger GPI Event',
        choices=SmartReader.START_TRIGGER_GPI_EVENT_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Start Trigger GPI Event'})
    )
    stop_trigger_type = forms.ChoiceField(
        label='Stop Trigger Type',
        choices=SmartReader.STOP_TRIGGER_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Stop Trigger Type'})
    )
    stop_trigger_duration = forms.IntegerField(
        label='Stop Trigger Duration',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Stop Trigger Duration'})
    )
    stop_trigger_timeout = forms.IntegerField(
        label='Stop Trigger Timeout',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Stop Trigger Timeout'})
    )
    stop_trigger_gpi_port = forms.ChoiceField(
        label='Stop Trigger GPI Port',
        choices=SmartReader.STOP_TRIGGER_GPI_PORT_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Stop Trigger GPI Port'})
    )
    stop_trigger_gpi_event = forms.ChoiceField(
        label='Stop Trigger GPI Event',
        choices=SmartReader.STOP_TRIGGER_GPI_EVENT_CHOICES,
        widget=forms.Select(attrs={'placeholder': 'Select Stop Trigger GPI Event'})
    )
    socket_server = forms.BooleanField(
        label='Socket Server',
        required=False,
        widget=forms.CheckboxInput()
    )
    socket_port = forms.IntegerField(
        label='Socket Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Socket Port'})
    )
    socket_command_server = forms.BooleanField(
        label='Socket Command Server',
        required=False,
        widget=forms.CheckboxInput()
    )
    socket_command_server_port = forms.IntegerField(
        label='Socket Command Server Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Socket Command Server Port'})
    )
    udp_server = forms.BooleanField(
        label='UDP Server',
        required=False,
        widget=forms.CheckboxInput()
    )
    udp_ip_address = forms.GenericIPAddressField(
        label='UDP IP Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter UDP IP Address'})
    )
    udp_reader_port = forms.IntegerField(
        label='UDP Reader Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter UDP Reader Port'})
    )
    udp_remote_ip_address = forms.GenericIPAddressField(
        label='UDP Remote IP Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter UDP Remote IP Address'})
    )
    udp_remote_port = forms.IntegerField(
        label='UDP Remote Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter UDP Remote Port'})
    )
    http_post_enabled = forms.BooleanField(
        label='HTTP Post Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    http_post_type = forms.IntegerField(
        label='HTTP Post Type',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter HTTP Post Type'})
    )
    http_post_interval_sec = forms.IntegerField(
        label='HTTP Post Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter HTTP Post Interval (sec)'})
    )
    http_post_url = forms.URLField(
        label='HTTP Post URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter HTTP Post URL'})
    )
    http_authentication_type = forms.CharField(
        label='HTTP Authentication Type',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Authentication Type'})
    )
    http_authentication_username = forms.CharField(
        label='HTTP Authentication Username',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Authentication Username'})
    )
    http_authentication_password = forms.CharField(
        label='HTTP Authentication Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter HTTP Authentication Password'})
    )
    http_authentication_token_api_enabled = forms.BooleanField(
        label='HTTP Token API Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    http_authentication_token_api_url = forms.URLField(
        label='HTTP Token API URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter HTTP Token API URL'})
    )
    http_authentication_token_api_body = forms.CharField(
        label='HTTP Token API Body',
        widget=forms.Textarea(attrs={'placeholder': 'Enter HTTP Token API Body'})
    )
    http_authentication_token_api_value = forms.CharField(
        label='HTTP Token API Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Token API Value'})
    )
    http_authentication_header = forms.CharField(
        label='HTTP Authentication Header',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Authentication Header'})
    )
    http_authentication_header_value = forms.CharField(
        label='HTTP Authentication Header Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Authentication Header Value'})
    )
    http_verify_post_http_return_code = forms.BooleanField(
        label='Verify HTTP Return Code',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_enabled = forms.BooleanField(
        label='MQTT Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_use_ssl = forms.BooleanField(
        label='Use SSL for MQTT',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_ssl_ca_certificate = forms.CharField(
        label='MQTT SSL CA Certificate',
        widget=forms.Textarea(attrs={'placeholder': 'Enter MQTT SSL CA Certificate'})
    )
    mqtt_ssl_client_certificate = forms.CharField(
        label='MQTT SSL Client Certificate',
        widget=forms.Textarea(attrs={'placeholder': 'Enter MQTT SSL Client Certificate'})
    )
    mqtt_ssl_client_certificate_password = forms.CharField(
        label='MQTT SSL Client Certificate Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter MQTT SSL Client Certificate Password'})
    )
    mqtt_broker_name = forms.CharField(
        label='MQTT Broker Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Broker Name'})
    )
    mqtt_broker_address = forms.GenericIPAddressField(
        label='MQTT Broker Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Broker Address'})
    )
    mqtt_broker_port = forms.IntegerField(
        label='MQTT Broker Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Broker Port'})
    )
    mqtt_broker_clean_session = forms.BooleanField(
        label='MQTT Clean Session',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_broker_keep_alive = forms.IntegerField(
        label='MQTT Keep Alive',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Keep Alive'})
    )
    mqtt_broker_debug = forms.BooleanField(
        label='MQTT Debug',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_tag_events_topic = forms.CharField(
        label='MQTT Tag Events Topic',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Tag Events Topic'})
    )
    mqtt_tag_events_qos = forms.IntegerField(
        label='MQTT Tag Events QoS',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Tag Events QoS'})
    )
    mqtt_tag_events_retain_messages = forms.BooleanField(
        label='Retain MQTT Tag Events Messages',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_management_events_topic = forms.CharField(
        label='MQTT Management Events Topic',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Management Events Topic'})
    )
    mqtt_management_events_qos = forms.IntegerField(
        label='MQTT Management Events QoS',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Management Events QoS'})
    )
    mqtt_management_events_retain_messages = forms.BooleanField(
        label='Retain MQTT Management Events Messages',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_metric_events_topic = forms.CharField(
        label='MQTT Metric Events Topic',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Metric Events Topic'})
    )
    mqtt_metric_events_qos = forms.IntegerField(
        label='MQTT Metric Events QoS',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Metric Events QoS'})
    )
    mqtt_metric_events_retain_messages = forms.BooleanField(
        label='Retain MQTT Metric Events Messages',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_management_command_topic = forms.CharField(
        label='MQTT Management Command Topic',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Management Command Topic'})
    )
    mqtt_management_command_qos = forms.IntegerField(
        label='MQTT Management Command QoS',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Management Command QoS'})
    )
    mqtt_management_command_retain_messages = forms.BooleanField(
        label='Retain MQTT Management Command Messages',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_management_response_topic = forms.CharField(
        label='MQTT Management Response Topic',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Management Response Topic'})
    )
    mqtt_management_response_qos = forms.IntegerField(
        label='MQTT Management Response QoS',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Management Response QoS'})
    )
    mqtt_management_response_retain_messages = forms.BooleanField(
        label='Retain MQTT Management Response Messages',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_control_command_topic = forms.CharField(
        label='MQTT Control Command Topic',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Control Command Topic'})
    )
    mqtt_control_command_qos = forms.IntegerField(
        label='MQTT Control Command QoS',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Control Command QoS'})
    )
    mqtt_control_command_retain_messages = forms.BooleanField(
        label='Retain MQTT Control Command Messages',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_control_response_topic = forms.CharField(
        label='MQTT Control Response Topic',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Control Response Topic'})
    )
    mqtt_control_response_qos = forms.IntegerField(
        label='MQTT Control Response QoS',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Control Response QoS'})
    )
    mqtt_control_response_retain_messages = forms.BooleanField(
        label='Retain MQTT Control Response Messages',
        required=False,
        widget=forms.CheckboxInput()
    )
    mqtt_lwt_topic = forms.CharField(
        label='MQTT Last Will and Testament Topic',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT LWT Topic'})
    )
    mqtt_lwt_qos = forms.IntegerField(
        label='MQTT LWT QoS',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT LWT QoS'})
    )
    mqtt_username = forms.CharField(
        label='MQTT Username',
        widget=forms.TextInput(attrs={'placeholder': 'Enter MQTT Username'})
    )
    mqtt_password = forms.CharField(
        label='MQTT Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter MQTT Password'})
    )
    mqtt_publish_interval_sec = forms.IntegerField(
        label='MQTT Publish Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter MQTT Publish Interval (sec)'})
    )
    mqtt_enable_smartreader_default_topics = forms.BooleanField(
        label='Enable SmartReader Default Topics',
        required=False,
        widget=forms.CheckboxInput()
    )
    is_cloud_interface = forms.BooleanField(
        label='Cloud Interface',
        required=False,
        widget=forms.CheckboxInput()
    )
    site = forms.CharField(
    label='Site',
    required=False,
    widget=forms.TextInput(attrs={'placeholder': 'Enter Site'})
    )

    site_enabled = forms.BooleanField(
        label='Site Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )

    low_duty_cycle_enabled = forms.BooleanField(
        label='Low Duty Cycle Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )

    empty_field_timeout = forms.IntegerField(
        label='Empty Field Timeout',
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Empty Field Timeout'})
    )

    field_ping_interval = forms.IntegerField(
        label='Field Ping Interval',
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Field Ping Interval'})
    )

    usb_flash_drive = forms.BooleanField(
        label='USB Flash Drive',
        required=False,
        widget=forms.CheckboxInput()
    )

    serial_port = forms.CharField(
        label='Serial Port',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter Serial Port'})
    )

    usb_hid = forms.BooleanField(
        label='USB HID',
        required=False,
        widget=forms.CheckboxInput()
    )

    data_prefix = forms.CharField(
        label='Data Prefix',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter Data Prefix'})
    )

    data_suffix = forms.CharField(
        label='Data Suffix',
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter Data Suffix'})
    )

    truncate_epc = forms.BooleanField(
        label='Truncate EPC',
        required=False,
        widget=forms.CheckboxInput()
    )

    truncate_start = forms.IntegerField(
        label='Truncate Start',
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Truncate Start'})
    )

    truncate_len = forms.IntegerField(
        label='Truncate Length',
        required=False,
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Truncate Length'})
    )

    http_verify_host = forms.BooleanField(
        label='HTTP Verify Host',
        required=False,
        widget=forms.CheckboxInput()
    )

    http_verify_peer = forms.BooleanField(
        label='HTTP Verify Peer',
        required=False,
        widget=forms.CheckboxInput()
    )

    max_tx_power_on_gpi_event_enabled = forms.BooleanField(
        label='Max TX Power on GPI Event Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )

    tag_validation_enabled = forms.BooleanField(
        label='Tag Validation Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )

    prompt_before_changing = forms.BooleanField(
        label='Prompt Before Changing',
        required=False,
        widget=forms.CheckboxInput()
    )
    ip_address_mode = forms.CharField(
        label='IP Address Mode',
        widget=forms.TextInput(attrs={'placeholder': 'Enter IP Address Mode'})
    )
    ip_address = forms.GenericIPAddressField(
        label='IP Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter IP Address'})
    )
    ip_mask = forms.GenericIPAddressField(
        label='IP Mask',
        widget=forms.TextInput(attrs={'placeholder': 'Enter IP Mask'})
    )
    gateway_address = forms.GenericIPAddressField(
        label='Gateway Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Gateway Address'})
    )
    broadcast_address = forms.GenericIPAddressField(
        label='Broadcast Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Broadcast Address'})
    )
    software_filter_enabled = forms.BooleanField(
        label='Software Filter Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_window_sec = forms.IntegerField(
        label='Software Filter Window (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Software Filter Window (sec)'})
    )
    software_filter_field = forms.IntegerField(
        label='Software Filter Field',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Software Filter Field'})
    )
    software_filter_read_count_timeout_enabled = forms.BooleanField(
        label='Read Count Timeout Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_read_count_timeout_seen_count = forms.IntegerField(
        label='Read Count Timeout Seen Count',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Read Count Timeout Seen Count'})
    )
    software_filter_read_count_timeout_interval_in_sec = forms.IntegerField(
        label='Read Count Timeout Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Read Count Timeout Interval (sec)'})
    )
    include_reader_name = forms.BooleanField(
        label='Include Reader Name',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_antenna_port = forms.BooleanField(
        label='Include Antenna Port',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_antenna_zone = forms.BooleanField(
        label='Include Antenna Zone',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_first_seen_timestamp = forms.BooleanField(
        label='Include First Seen Timestamp',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_peak_rssi = forms.BooleanField(
        label='Include Peak RSSI',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_rf_phase_angle = forms.BooleanField(
        label='Include RF Phase Angle',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_rf_doppler_frequency = forms.BooleanField(
        label='Include RF Doppler Frequency',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_rf_channel_index = forms.BooleanField(
        label='Include RF Channel Index',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_gpi_event = forms.BooleanField(
        label='Include GPI Event',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_inventory_status_event = forms.BooleanField(
        label='Include Inventory Status Event',
        required=False,
        widget=forms.CheckboxInput()
    )
    include_inventory_status_event_id = forms.IntegerField(
        label='Inventory Status Event ID',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Inventory Status Event ID'})
    )
    include_inventory_status_event_total_count = forms.IntegerField(
        label='Inventory Status Event Total Count',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Inventory Status Event Total Count'})
    )
    include_tid = forms.BooleanField(
        label='Include TID',
        required=False,
        widget=forms.CheckboxInput()
    )
    tid_word_start = forms.IntegerField(
        label='TID Word Start',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TID Word Start'})
    )
    tid_word_count = forms.IntegerField(
        label='TID Word Count',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TID Word Count'})
    )
    include_user_memory = forms.BooleanField(
        label='Include User Memory',
        required=False,
        widget=forms.CheckboxInput()
    )
    user_memory_word_start = forms.IntegerField(
        label='User Memory Word Start',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter User Memory Word Start'})
    )
    user_memory_word_count = forms.IntegerField(
        label='User Memory Word Count',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter User Memory Word Count'})
    )
    heartbeat_enabled = forms.BooleanField(
        label='Heartbeat Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    heartbeat_period_sec = forms.IntegerField(
        label='Heartbeat Period (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Heartbeat Period (sec)'})
    )
    heartbeat_url = forms.URLField(
        label='Heartbeat URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter Heartbeat URL'})
    )
    heartbeat_http_authentication_type = forms.CharField(
        label='Heartbeat HTTP Authentication Type',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Authentication Type'})
    )
    heartbeat_http_authentication_username = forms.CharField(
        label='Heartbeat HTTP Authentication Username',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Authentication Username'})
    )
    heartbeat_http_authentication_password = forms.CharField(
        label='Heartbeat HTTP Authentication Password',
        widget=forms.PasswordInput(attrs={'placeholder': 'Enter HTTP Authentication Password'})
    )
    heartbeat_http_authentication_token_api_enabled = forms.BooleanField(
        label='HTTP Token API Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    heartbeat_http_authentication_token_api_url = forms.URLField(
        label='HTTP Token API URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter HTTP Token API URL'})
    )
    heartbeat_http_authentication_token_api_body = forms.CharField(
        label='HTTP Token API Body',
        widget=forms.Textarea(attrs={'placeholder': 'Enter HTTP Token API Body'})
    )
    heartbeat_http_authentication_token_api_username_field = forms.CharField(
        label='HTTP Token API Username Field',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Token API Username Field'})
    )
    heartbeat_http_authentication_token_api_username_value = forms.CharField(
        label='HTTP Token API Username Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Token API Username Value'})
    )
    heartbeat_http_authentication_token_api_password_field = forms.CharField(
        label='HTTP Token API Password Field',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Token API Password Field'})
    )
    heartbeat_http_authentication_token_api_password_value = forms.CharField(
        label='HTTP Token API Password Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Token API Password Value'})
    )
    heartbeat_http_authentication_token_api_value = forms.CharField(
        label='HTTP Token API Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter HTTP Token API Value'})
    )  
    is_log_file_enabled = forms.BooleanField(
        label='Log File Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    operating_region = forms.CharField(
        label='Operating Region',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Operating Region'})
    )
    system_image_upgrade_url = forms.URLField(
        label='System Image Upgrade URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter System Image Upgrade URL'})
    )
    system_disable_image_fallback_status = forms.BooleanField(
        label='Disable Image Fallback Status',
        required=False,
        widget=forms.CheckboxInput()
    )
    smartreader_enabled_for_management_only = forms.BooleanField(
        label='Enabled for Management Only',
        required=False,
        widget=forms.CheckboxInput()
    )
    toi_validation_enabled = forms.BooleanField(
        label='TOI Validation Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    toi_validation_url = forms.URLField(
        label='TOI Validation URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter TOI Validation URL'})
    )
    toi_validation_gpo_duration = forms.IntegerField(
        label='TOI Validation GPO Duration',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TOI Validation GPO Duration'})
    )
    toi_gpo_ok = forms.IntegerField(
        label='TOI GPO OK',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TOI GPO OK'})
    )
    toi_gpo_nok = forms.IntegerField(
        label='TOI GPO NOK',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TOI GPO NOK'})
    )
    toi_gpo_error = forms.IntegerField(
        label='TOI GPO Error',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TOI GPO Error'})
    )
    toi_gpi = forms.IntegerField(
        label='TOI GPI',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TOI GPI'})
    )
    toi_gpo_priority = forms.IntegerField(
        label='TOI GPO Priority',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TOI GPO Priority'})
    )
    toi_gpo_mode = forms.IntegerField(
        label='TOI GPO Mode',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter TOI GPO Mode'})
    )
    write_usb_json = forms.BooleanField(
        label='Write USB JSON',
        required=False,
        widget=forms.CheckboxInput()
    )
    reporting_interval_seconds = forms.IntegerField(
        label='Reporting Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Reporting Interval (sec)'})
    )
    tag_cache_size = forms.IntegerField(
        label='Tag Cache Size',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Tag Cache Size'})
    )
    antenna_identifier = forms.CharField(
        label='Antenna Identifier',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Antenna Identifier'})
    )
    tag_identifier = forms.CharField(
        label='Tag Identifier',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Tag Identifier'})
    )
    positioning_epcs_enabled = forms.BooleanField(
        label='Positioning EPCs Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    positioning_antenna_ports = forms.CharField(
        label='Positioning Antenna Ports',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Positioning Antenna Ports'})
    )
    positioning_epcs_header_list = forms.CharField(
        label='Positioning EPCs Header List',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Positioning EPCs Header List'})
    )
    positioning_epcs_filter = forms.CharField(
        label='Positioning EPCs Filter',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Positioning EPCs Filter'})
    )
    positioning_expiration_in_sec = forms.IntegerField(
        label='Positioning Expiration (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Positioning Expiration (sec)'})
    )
    positioning_report_interval_in_sec = forms.IntegerField(
        label='Positioning Report Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Positioning Report Interval (sec)'})
    )
    enable_unique_tag_read = forms.BooleanField(
        label='Enable Unique Tag Read',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_antenna_task = forms.BooleanField(
        label='Enable Antenna Task',
        required=False,
        widget=forms.CheckboxInput()
    )
    package_headers = forms.CharField(
        label='Package Headers',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Package Headers'})
    )
    enable_partial_validation = forms.BooleanField(
        label='Enable Partial Validation',
        required=False,
        widget=forms.CheckboxInput()
    )
    validation_acceptance_threshold = forms.IntegerField(
        label='Validation Acceptance Threshold',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Validation Acceptance Threshold'})
    )
    validation_acceptance_threshold_timeout = forms.IntegerField(
        label='Validation Acceptance Threshold Timeout (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Validation Acceptance Threshold Timeout'})
    )
    publish_full_shipment_validation_list_on_acceptance_threshold = forms.BooleanField(
        label='Publish Full Shipment Validation List on Acceptance Threshold',
        required=False,
        widget=forms.CheckboxInput()
    )
    publish_single_time_on_acceptance_threshold = forms.BooleanField(
        label='Publish Single Time on Acceptance Threshold',
        required=False,
        widget=forms.CheckboxInput()
    )
    active_plugin = forms.CharField(
        label='Active Plugin',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Active Plugin'})
    )
    plugin_server = forms.CharField(
        label='Plugin Server',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Plugin Server'})
    )
    enable_plugin_shipment_verification = forms.BooleanField(
        label='Enable Plugin Shipment Verification',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_include_epcs_header_list_enabled = forms.BooleanField(
        label='Software Filter Include EPCs Header List Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_include_epcs_header_list = forms.CharField(
        label='Software Filter Include EPCs Header List',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Include EPCs Header List'})
    )
    software_filter_tag_id_enabled = forms.BooleanField(
        label='Software Filter Tag ID Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_tag_id_match = forms.CharField(
        label='Software Filter Tag ID Match',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Match'})
    )
    software_filter_tag_id_operation = forms.CharField(
        label='Software Filter Tag ID Operation',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Operation'})
    )
    software_filter_tag_id_value_or_pattern = forms.CharField(
        label='Software Filter Tag ID Value or Pattern',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Value or Pattern'})
    )
    rci_spot_report_enabled = forms.BooleanField(
        label='RCI Spot Report Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_pc = forms.BooleanField(
        label='RCI Spot Report Include PC',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_scheme = forms.BooleanField(
        label='RCI Spot Report Include Scheme',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_epc_uri = forms.BooleanField(
        label='RCI Spot Report Include EPC URI',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_ant = forms.BooleanField(
        label='RCI Spot Report Include Antenna',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_dwn_cnt = forms.BooleanField(
        label='RCI Spot Report Include DWN CNT',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_inv_cnt = forms.BooleanField(
        label='RCI Spot Report Include INV CNT',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_phase = forms.BooleanField(
        label='RCI Spot Report Include Phase',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_prof = forms.BooleanField(
        label='RCI Spot Report Include Prof',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_range = forms.BooleanField(
        label='RCI Spot Report Include Range',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_rssi = forms.BooleanField(
        label='RCI Spot Report Include RSSI',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_rz = forms.BooleanField(
        label='RCI Spot Report Include RZ',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_spot = forms.BooleanField(
        label='RCI Spot Report Include Spot',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_time_stamp = forms.BooleanField(
        label='RCI Spot Report Include Timestamp',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_opc_ua_client = forms.BooleanField(
        label='Enable OPC UA Client',
        required=False,
        widget=forms.CheckboxInput()
    )
    opc_ua_connection_name = forms.CharField(
        label='OPC UA Connection Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Connection Name'})
    )
    opc_ua_connection_publisher_id = forms.IntegerField(
        label='OPC UA Connection Publisher ID',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Connection Publisher ID'})
    )
    opc_ua_connection_url = forms.URLField(
        label='OPC UA Connection URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter OPC UA Connection URL'})
    )
    opc_ua_connection_discovery_address = forms.URLField(
        label='OPC UA Connection Discovery Address',
        widget=forms.URLInput(attrs={'placeholder': 'Enter OPC UA Connection Discovery Address'})
    )
    opc_ua_writer_group_name = forms.CharField(
        label='OPC UA Writer Group Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Writer Group Name'})
    )
    opc_ua_writer_group_id = forms.IntegerField(
        label='OPC UA Writer Group ID',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Writer Group ID'})
    )
    opc_ua_writer_publishing_interval = forms.IntegerField(
        label='OPC UA Writer Publishing Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Writer Publishing Interval (sec)'})
    )
    opc_ua_writer_keep_alive_time = forms.IntegerField(
        label='OPC UA Writer Keep Alive Time (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Writer Keep Alive Time (sec)'})
    )
    opc_ua_writer_max_network_message_size = forms.IntegerField(
        label='OPC UA Writer Max Network Message Size',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Writer Max Network Message Size'})
    )
    opc_ua_writer_header_layout_uri = forms.CharField(
        label='OPC UA Writer Header Layout URI',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Writer Header Layout URI'})
    )
    opc_ua_data_set_writer_name = forms.CharField(
        label='OPC UA Data Set Writer Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Data Set Writer Name'})
    )
    opc_ua_data_set_writer_id = forms.IntegerField(
        label='OPC UA Data Set Writer ID',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Data Set Writer ID'})
    )
    opc_ua_data_set_name = forms.CharField(
        label='OPC UA Data Set Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Data Set Name'})
    )
    opc_ua_data_set_key_frame_count = forms.IntegerField(
        label='OPC UA Data Set Key Frame Count',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Data Set Key Frame Count'})
    )
    enable_plugin = forms.BooleanField(
        label='Enable Plugin',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_barcode_tcp = forms.BooleanField(
        label='Enable Barcode TCP',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_barcode_serial = forms.BooleanField(
        label='Enable Barcode Serial',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_barcode_hid = forms.BooleanField(
        label='Enable Barcode HID',
        required=False,
        widget=forms.CheckboxInput()
    )
    group_events_on_inventory_status = forms.BooleanField(
        label='Group Events on Inventory Status',
        required=False,
        widget=forms.CheckboxInput()
    )    
    enable_validation = forms.BooleanField(
        label='Enable Validation',
        required=False,
        widget=forms.CheckboxInput()
    )
    require_unique_product_code = forms.BooleanField(
        label='Require Unique Product Code',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_tag_event_stream = forms.BooleanField(
        label='Enable Tag Event Stream',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_summary_stream = forms.BooleanField(
        label='Enable Summary Stream',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_external_api_verification = forms.BooleanField(
        label='Enable External API Verification',
        required=False,
        widget=forms.CheckboxInput()
    )
    external_api_verification_search_order_url = forms.URLField(
        label='External API Verification Search Order URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Search Order URL'})
    )
    external_api_verification_search_product_url = forms.URLField(
        label='External API Verification Search Product URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Search Product URL'})
    )
    external_api_verification_publish_data_url = forms.URLField(
        label='External API Verification Publish Data URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Publish Data URL'})
    )
    external_api_verification_change_order_status_url = forms.URLField(
        label='External API Verification Change Order Status URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Change Order Status URL'})
    )
    external_api_verification_http_header_name = forms.CharField(
        label='External API Verification HTTP Header Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter External API Verification HTTP Header Name'})
    )
    external_api_verification_http_header_value = forms.CharField(
        label='External API Verification HTTP Header Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter External API Verification HTTP Header Value'})
    )
    external_api_verification_auth_login_url = forms.URLField(
        label='External API Verification Auth Login URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Auth Login URL'})
    )
    network_proxy = forms.CharField(
        label='Network Proxy',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Network Proxy'})
    )
    network_proxy_port = forms.IntegerField(
        label='Network Proxy Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Network Proxy Port'})
    )
    enable_tag_events_list_batch = forms.BooleanField(
        label='Enable Tag Events List Batch',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_tag_events_list_batch_publishing = forms.BooleanField(
        label='Enable Tag Events List Batch Publishing',
        required=False,
        widget=forms.CheckboxInput()
    )
    update_tag_events_list_batch_on_change = forms.BooleanField(
        label='Update Tag Events List Batch on Change',
        required=False,
        widget=forms.CheckboxInput()
    )
    update_tag_events_list_batch_on_change_interval_in_sec = forms.IntegerField(
        label='Update Tag Events List Batch on Change Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Update Tag Events List Batch on Change Interval (sec)'})
    )
    filter_tag_events_list_batch_on_change_based_on_antenna_zone = forms.BooleanField(
        label='Filter Tag Events List Batch on Change Based on Antenna Zone',
        required=False,
        widget=forms.CheckboxInput()
    )
    tag_presence_timeout_enabled = forms.BooleanField(
        label='Tag Presence Timeout Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    tag_presence_timeout_in_sec = forms.IntegerField(
        label='Tag Presence Timeout (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Tag Presence Timeout (sec)'})
    )
    package_headers = forms.CharField(
        label='Package Headers',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Package Headers'})
    )
    enable_partial_validation = forms.BooleanField(
        label='Enable Partial Validation',
        required=False,
        widget=forms.CheckboxInput()
    )
    validation_acceptance_threshold = forms.IntegerField(
        label='Validation Acceptance Threshold',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Validation Acceptance Threshold'})
    )
    validation_acceptance_threshold_timeout = forms.IntegerField(
        label='Validation Acceptance Threshold Timeout (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Validation Acceptance Threshold Timeout'})
    )
    publish_full_shipment_validation_list_on_acceptance_threshold = forms.BooleanField(
        label='Publish Full Shipment Validation List on Acceptance Threshold',
        required=False,
        widget=forms.CheckboxInput()
    )
    publish_single_time_on_acceptance_threshold = forms.BooleanField(
        label='Publish Single Time on Acceptance Threshold',
        required=False,
        widget=forms.CheckboxInput()
    )
    active_plugin = forms.CharField(
        label='Active Plugin',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Active Plugin'})
    )
    plugin_server = forms.CharField(
        label='Plugin Server',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Plugin Server'})
    )
    enable_plugin_shipment_verification = forms.BooleanField(
        label='Enable Plugin Shipment Verification',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_include_epcs_header_list_enabled = forms.BooleanField(
        label='Software Filter Include EPCs Header List Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_include_epcs_header_list = forms.CharField(
        label='Software Filter Include EPCs Header List',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Include EPCs Header List'})
    )
    software_filter_tag_id_enabled = forms.BooleanField(
        label='Software Filter Tag ID Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_tag_id_match = forms.CharField(
        label='Software Filter Tag ID Match',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Match'})
    )
    software_filter_tag_id_operation = forms.CharField(
        label='Software Filter Tag ID Operation',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Operation'})
    )
    software_filter_tag_id_value_or_pattern = forms.CharField(
        label='Software Filter Tag ID Value or Pattern',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Value or Pattern'})
    )
    is_log_file_enabled = forms.BooleanField(
        label='Log File Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_enabled = forms.BooleanField(
        label='RCI Spot Report Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_pc = forms.BooleanField(
        label='RCI Spot Report Include PC',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_scheme = forms.BooleanField(
        label='RCI Spot Report Include Scheme',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_epc_uri = forms.BooleanField(
        label='RCI Spot Report Include EPC URI',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_ant = forms.BooleanField(
        label='RCI Spot Report Include Antenna',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_dwn_cnt = forms.BooleanField(
        label='RCI Spot Report Include DWN CNT',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_inv_cnt = forms.BooleanField(
        label='RCI Spot Report Include INV CNT',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_phase = forms.BooleanField(
        label='RCI Spot Report Include Phase',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_prof = forms.BooleanField(
        label='RCI Spot Report Include Prof',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_range = forms.BooleanField(
        label='RCI Spot Report Include Range',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_rssi = forms.BooleanField(
        label='RCI Spot Report Include RSSI',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_rz = forms.BooleanField(
        label='RCI Spot Report Include RZ',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_spot = forms.BooleanField(
        label='RCI Spot Report Include Spot',
        required=False,
        widget=forms.CheckboxInput()
    )
    rci_spot_report_include_time_stamp = forms.BooleanField(
        label='RCI Spot Report Include Timestamp',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_opc_ua_client = forms.BooleanField(
        label='Enable OPC UA Client',
        required=False,
        widget=forms.CheckboxInput()
    )
    opc_ua_connection_name = forms.CharField(
        label='OPC UA Connection Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Connection Name'})
    )
    opc_ua_connection_publisher_id = forms.IntegerField(
        label='OPC UA Connection Publisher ID',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Connection Publisher ID'})
    )
    opc_ua_connection_url = forms.URLField(
        label='OPC UA Connection URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter OPC UA Connection URL'})
    )
    opc_ua_connection_discovery_address = forms.URLField(
        label='OPC UA Connection Discovery Address',
        widget=forms.URLInput(attrs={'placeholder': 'Enter OPC UA Connection Discovery Address'})
    )
    opc_ua_writer_group_name = forms.CharField(
        label='OPC UA Writer Group Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Writer Group Name'})
    )
    opc_ua_writer_group_id = forms.IntegerField(
        label='OPC UA Writer Group ID',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Writer Group ID'})
    )
    opc_ua_writer_publishing_interval = forms.IntegerField(
        label='OPC UA Writer Publishing Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Writer Publishing Interval (sec)'})
    )
    opc_ua_writer_keep_alive_time = forms.IntegerField(
        label='OPC UA Writer Keep Alive Time (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Writer Keep Alive Time (sec)'})
    )
    opc_ua_writer_max_network_message_size = forms.IntegerField(
        label='OPC UA Writer Max Network Message Size',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Writer Max Network Message Size'})
    )
    opc_ua_writer_header_layout_uri = forms.CharField(
        label='OPC UA Writer Header Layout URI',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Writer Header Layout URI'})
    )
    opc_ua_data_set_writer_name = forms.CharField(
        label='OPC UA Data Set Writer Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Data Set Writer Name'})
    )
    opc_ua_data_set_writer_id = forms.IntegerField(
        label='OPC UA Data Set Writer ID',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Data Set Writer ID'})
    )
    opc_ua_data_set_name = forms.CharField(
        label='OPC UA Data Set Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter OPC UA Data Set Name'})
    )
    opc_ua_data_set_key_frame_count = forms.IntegerField(
        label='OPC UA Data Set Key Frame Count',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter OPC UA Data Set Key Frame Count'})
    )
    enable_plugin = forms.BooleanField(
        label='Enable Plugin',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_barcode_tcp = forms.BooleanField(
        label='Enable Barcode TCP',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_barcode_serial = forms.BooleanField(
        label='Enable Barcode Serial',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_barcode_hid = forms.BooleanField(
        label='Enable Barcode HID',
        required=False,
        widget=forms.CheckboxInput()
    )
    group_events_on_inventory_status = forms.BooleanField(
        label='Group Events on Inventory Status',
        required=False,
        widget=forms.CheckboxInput()
    )
    barcode_tcp_address = forms.CharField(
        label='Barcode TCP Address',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Barcode TCP Address'})
    )
    barcode_tcp_port = forms.IntegerField(
        label='Barcode TCP Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Barcode TCP Port'})
    )
    barcode_tcp_len = forms.IntegerField(
        label='Barcode TCP Length',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Barcode TCP Length'})
    )
    barcode_tcp_no_data_string = forms.CharField(
        label='Barcode TCP No Data String',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Barcode TCP No Data String'})
    )
    barcode_process_no_data_string = forms.BooleanField(
        label='Process No Data String',
        required=False,
        widget=forms.CheckboxInput()
    )
    barcode_enable_queue = forms.BooleanField(
        label='Enable Barcode Queue',
        required=False,
        widget=forms.CheckboxInput()
    )
    barcode_line_end = forms.IntegerField(
        label='Barcode Line End',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Barcode Line End'})
    )
    enable_validation = forms.BooleanField(
        label='Enable Validation',
        required=False,
        widget=forms.CheckboxInput()
    )
    require_unique_product_code = forms.BooleanField(
        label='Require Unique Product Code',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_tag_event_stream = forms.BooleanField(
        label='Enable Tag Event Stream',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_summary_stream = forms.BooleanField(
        label='Enable Summary Stream',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_external_api_verification = forms.BooleanField(
        label='Enable External API Verification',
        required=False,
        widget=forms.CheckboxInput()
    )
    external_api_verification_search_order_url = forms.URLField(
        label='External API Verification Search Order URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Search Order URL'})
    )
    external_api_verification_search_product_url = forms.URLField(
        label='External API Verification Search Product URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Search Product URL'})
    )
    external_api_verification_publish_data_url = forms.URLField(
        label='External API Verification Publish Data URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Publish Data URL'})
    )
    external_api_verification_change_order_status_url = forms.URLField(
        label='External API Verification Change Order Status URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Change Order Status URL'})
    )
    external_api_verification_http_header_name = forms.CharField(
        label='External API Verification HTTP Header Name',
        widget=forms.TextInput(attrs={'placeholder': 'Enter External API Verification HTTP Header Name'})
    )
    external_api_verification_http_header_value = forms.CharField(
        label='External API Verification HTTP Header Value',
        widget=forms.TextInput(attrs={'placeholder': 'Enter External API Verification HTTP Header Value'})
    )
    external_api_verification_auth_login_url = forms.URLField(
        label='External API Verification Auth Login URL',
        widget=forms.URLInput(attrs={'placeholder': 'Enter External API Verification Auth Login URL'})
    )
    network_proxy = forms.CharField(
        label='Network Proxy',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Network Proxy'})
    )
    network_proxy_port = forms.IntegerField(
        label='Network Proxy Port',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Network Proxy Port'})
    )
    enable_tag_events_list_batch = forms.BooleanField(
        label='Enable Tag Events List Batch',
        required=False,
        widget=forms.CheckboxInput()
    )
    enable_tag_events_list_batch_publishing = forms.BooleanField(
        label='Enable Tag Events List Batch Publishing',
        required=False,
        widget=forms.CheckboxInput()
    )
    cleanup_tag_events_list_batch_on_reload = forms.BooleanField(
        label='Cleanup Tag Events List Batch on Reload',
        required=False,
        widget=forms.CheckboxInput()
    )
    update_tag_events_list_batch_on_change = forms.BooleanField(
        label='Update Tag Events List Batch on Change',
        required=False,
        widget=forms.CheckboxInput()
    )
    update_tag_events_list_batch_on_change_interval_in_sec = forms.IntegerField(
        label='Update Tag Events List Batch on Change Interval (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Update Tag Events List Batch on Change Interval (sec)'})
    )
    filter_tag_events_list_batch_on_change_based_on_antenna_zone = forms.BooleanField(
        label='Filter Tag Events List Batch on Change Based on Antenna Zone',
        required=False,
        widget=forms.CheckboxInput()
    )
    tag_presence_timeout_enabled = forms.BooleanField(
        label='Tag Presence Timeout Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    tag_presence_timeout_in_sec = forms.IntegerField(
        label='Tag Presence Timeout (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Tag Presence Timeout (sec)'})
    )
    package_headers = forms.CharField(
        label='Package Headers',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Package Headers'})
    )
    enable_partial_validation = forms.BooleanField(
        label='Enable Partial Validation',
        required=False,
        widget=forms.CheckboxInput()
    )
    validation_acceptance_threshold = forms.IntegerField(
        label='Validation Acceptance Threshold',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Validation Acceptance Threshold'})
    )
    validation_acceptance_threshold_timeout = forms.IntegerField(
        label='Validation Acceptance Threshold Timeout (sec)',
        widget=forms.NumberInput(attrs={'placeholder': 'Enter Validation Acceptance Threshold Timeout'})
    )
    publish_full_shipment_validation_list_on_acceptance_threshold = forms.BooleanField(
        label='Publish Full Shipment Validation List on Acceptance Threshold',
        required=False,
        widget=forms.CheckboxInput()
    )
    publish_single_time_on_acceptance_threshold = forms.BooleanField(
        label='Publish Single Time on Acceptance Threshold',
        required=False,
        widget=forms.CheckboxInput()
    )
    active_plugin = forms.CharField(
        label='Active Plugin',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Active Plugin'})
    )
    plugin_server = forms.CharField(
        label='Plugin Server',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Plugin Server'})
    )
    enable_plugin_shipment_verification = forms.BooleanField(
        label='Enable Plugin Shipment Verification',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_include_epcs_header_list_enabled = forms.BooleanField(
        label='Software Filter Include EPCs Header List Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_include_epcs_header_list = forms.CharField(
        label='Software Filter Include EPCs Header List',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Include EPCs Header List'})
    )
    software_filter_tag_id_enabled = forms.BooleanField(
        label='Software Filter Tag ID Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    software_filter_tag_id_match = forms.CharField(
        label='Software Filter Tag ID Match',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Match'})
    )
    software_filter_tag_id_operation = forms.CharField(
        label='Software Filter Tag ID Operation',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Operation'})
    )
    software_filter_tag_id_value_or_pattern = forms.CharField(
        label='Software Filter Tag ID Value or Pattern',
        widget=forms.TextInput(attrs={'placeholder': 'Enter Software Filter Tag ID Value or Pattern'})
    )
    parse_sgtin_enabled = forms.BooleanField(
        label='GS1 Tag Data Parser (SGTIN) Enabled',
        required=False,
        widget=forms.CheckboxInput()
    )
    parse_sgtin_include_key_type = forms.BooleanField(
        label='Include GS1 Key Type in parsed data',
        required=False,
        widget=forms.CheckboxInput()
    )
    parse_sgtin_include_key_type = forms.BooleanField(
        label='Include GS1 Key Type in parsed data',
        required=False,
        widget=forms.CheckboxInput()
    )
    parse_gtin_include_serial = forms.BooleanField(
        label='Include GS1 Serial in parsed data',
        required=False,
        widget=forms.CheckboxInput()
    )
    parse_gtin_include_pure_identity = forms.BooleanField(
        label='Include Pure Identity in parsed data',
        required=False,
        widget=forms.CheckboxInput()       
    )
    gtin_output_type = forms.DecimalField(
    label='GTIN Output type',
    required=False,
    initial=0,
    widget=forms.NumberInput(attrs={'placeholder': 'Enter GTIN Output Type'})
    )


class SmartReaderFilterForm(forms.Form):
    reader_name = forms.CharField(required=False, label="Reader Name")
    status = forms.ChoiceField(choices=[('', '---')] + SmartReader.STATUS_CHOICES, required=False, label="Status")

class MQTTConfigurationForm(forms.ModelForm):
    class Meta:
        model = MQTTConfiguration
        fields = [
            'enable_mqtt',
            'enable_batch_list_reporting',
            'clear_batch_list_on_reload',
            'publish_batch_list_on_change',
            'publish_batch_list_on_change_interval',
            'enable_publish_interval_for_batch_lists',
            'publish_interval',
            'filter_batch_updates_based_on_antenna_zone_grouping',
            'broker_username',
            'broker_password',
            'broker_hostname',
            'broker_port',
            'mqtt_broker_keepalive',
            'mqtt_broker_clean_session',
            'mqtt_broker_protocol',
            'mqtt_tag_events_topic',
            'mqtt_tag_events_qos_level',
            'mqtt_tag_events_retain',
            'mqtt_management_events_topic',
            'mqtt_management_events_qos_level',
            'mqtt_management_events_retain',
            'mqtt_metrics_topic',
            'mqtt_metrics_qos_level',
            'mqtt_metrics_retain',
            'enable_command_receiver',
            'mqtt_management_command_topic',
            'mqtt_management_command_qos_level',
            'mqtt_management_command_retain',
            'mqtt_management_command_response_topic',
            'mqtt_management_command_response_qos_level',
            'mqtt_control_command_topic',
            'mqtt_control_command_qos_level',
            'mqtt_control_command_retain',
            'mqtt_control_command_response_topic',
            'mqtt_control_command_response_qos_level',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

class MqttCommandTemplateForm(forms.ModelForm):
    class Meta:
        model = MqttCommandTemplate
        fields = ['name', 'description', 'template_content']

class MqttCommandForm(forms.ModelForm):
    class Meta:
        model = MQTTCommand
        fields = '__all__'  # Include all fields of MQTTCommand

class CommandSendForm(forms.Form):
    command_template = forms.ModelChoiceField(
        queryset=MqttCommandTemplate.objects.all(),
        label="Command Template",
        required=True
    )
    smartreaders = forms.ModelMultipleChoiceField(
        queryset=SmartReader.objects.all(),
        label="Smart Readers",
        required=True
    )