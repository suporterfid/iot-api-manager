from django.urls import path

from .views import (
    MQTTConfigurationListView, MQTTConfigurationDetailView, MQTTConfigurationCreateView, MQTTConfigurationUpdateView, MQTTConfigurationDeleteView,
    SmartReaderListView, SmartReaderDetailView, SmartReaderCreateView, SmartReaderUpdateView, SmartReaderDeleteView,
    AlertRuleListView, AlertRuleCreateView, AlertRuleUpdateView, AlertRuleDeleteView, AlertRuleWizard,
    AlertActionListView, AlertActionCreateView, AlertActionUpdateView, AlertActionDeleteView,
    MqttCommandTemplateListView, MqttCommandTemplateCreateView, MqttCommandTemplateUpdateView, MqttCommandTemplateDetailView, MqttCommandTemplateDeleteView,
    MQTTCommandListView, MqttCommandCreateView, MqttCommandUpdateView, MqttCommandDetailView, MqttCommandDeleteView,
    CommandSendView, AlertConditionListView, AlertConditionCreateView, AlertConditionUpdateView, AlertConditionDeleteView,
    test_alert_action
)

urlpatterns = [
    # MQTT Configurations
    path('mqtt-configurations/', MQTTConfigurationListView.as_view(), name='mqttconfiguration_list'),
    path('mqtt-configurations/<int:pk>/', MQTTConfigurationDetailView.as_view(), name='mqttconfiguration_detail'),
    path('mqtt-configurations/create/', MQTTConfigurationCreateView.as_view(), name='mqttconfiguration_create'),
    path('mqtt-configurations/<int:pk>/update/', MQTTConfigurationUpdateView.as_view(), name='mqttconfiguration_update'),
    path('mqtt-configurations/<int:pk>/delete/', MQTTConfigurationDeleteView.as_view(), name='mqttconfiguration_delete'),

    # SmartReaders
    path('', SmartReaderListView.as_view(), name='smartreader_list'),
    path('<int:pk>/', SmartReaderDetailView.as_view(), name='smartreader_detail'),
    path('create/', SmartReaderCreateView.as_view(), name='smartreader_create'),
    path('<int:pk>/update/', SmartReaderUpdateView.as_view(), name='smartreader_update'),
    path('<int:pk>/delete/', SmartReaderDeleteView.as_view(), name='smartreader_delete'),

    #Alert Actions
    path('alert-actions/', AlertActionListView.as_view(), name='alert_action_list'),
    path('alert-actions/create/', AlertActionCreateView.as_view(), name='alert_action_create'),
    path('alert-actions/<int:pk>/update/', AlertActionUpdateView.as_view(), name='alert_action_update'),
    path('alert-actions/<int:pk>/delete/', AlertActionDeleteView.as_view(), name='alert_action_delete'),

    # Alert Rules
    path('alerts/', AlertRuleListView.as_view(), name='alert_rule_list'),
    path('alerts/create/', AlertRuleWizard.as_view(), name='alert_rule_create'),
    path('alerts/<int:pk>/update/', AlertRuleUpdateView.as_view(), name='alert_rule_update'),
    path('alerts/<int:pk>/delete/', AlertRuleDeleteView.as_view(), name='alert_rule_delete'),

    # Alert Condition
    path('alert-conditions/', AlertConditionListView.as_view(), name='alert_condition_list'),
    path('alert-conditions/create/', AlertConditionCreateView.as_view(), name='alert_condition_create'),
    path('alert-conditions/<int:pk>/update/', AlertConditionUpdateView.as_view(), name='alert_condition_update'),
    path('alert-conditions/<int:pk>/delete/', AlertConditionDeleteView.as_view(), name='alert_condition_delete'),

    # MQTT Command Templates
    path('mqtt-command-templates/', MqttCommandTemplateListView.as_view(), name='mqttcommandtemplate_list'),
    path('mqtt-command-templates/create/', MqttCommandTemplateCreateView.as_view(), name='mqttcommandtemplate_create'),
    path('mqtt-command-templates/<int:pk>/', MqttCommandTemplateDetailView.as_view(), name='mqttcommandtemplate_detail'),
    path('mqtt-command-templates/<int:pk>/update/', MqttCommandTemplateUpdateView.as_view(), name='mqttcommandtemplate_update'),
    path('mqtt-command-templates/<int:pk>/delete/', MqttCommandTemplateDeleteView.as_view(), name='mqttcommandtemplate_delete'),

    # MQTT Commands
    path('mqtt-commands/', MQTTCommandListView.as_view(), name='mqttcommand_list'),
    path('mqtt-commands/create/', MqttCommandCreateView.as_view(), name='mqttcommand_create'),
    path('mqtt-commands/<int:pk>/', MqttCommandDetailView.as_view(), name='mqttcommand_detail'),
    path('mqtt-commands/<int:pk>/update/', MqttCommandUpdateView.as_view(), name='mqttcommand_update'),
    path('mqtt-commands/<int:pk>/delete/', MqttCommandDeleteView.as_view(), name='mqttcommand_delete'),

    # Command Send
    path('command/send/', CommandSendView.as_view(), name='command_send'),

    # Test Alert Action
    path('test-alert-action/', test_alert_action, name='test_alert_action'),
]

