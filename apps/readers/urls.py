from django.urls import path
from . import views
from .views import (
    dashboard, reader_list, reader_create, reader_update, 
    reader_delete, start_preset, stop_preset, webhook_receiver, 
    tag_event_list, tag_event_details, export_tag_events, PresetListView, PresetCreateView, 
    PresetUpdateView, PresetDeleteView, query_presets, get_preset_details,
    PresetTemplateListView, PresetTemplateCreateView,
    PresetTemplateUpdateView, PresetTemplateDeleteView,
    WebhookTemplateListView, WebhookTemplateCreateView, WebhookTemplateUpdateView, WebhookTemplateDeleteView,
    MqttTemplateListView, MqttTemplateCreateView, MqttTemplateUpdateView, MqttTemplateDeleteView,
    WebhookTemplateResultListView, WebhookTemplateResultRetryView,
    MQTTTemplateResultListView, MQTTTemplateResultRetryView, view_logs,
    TagTraceabilityListView, ReadPointListView, ReadPointCreateView, 
    ReadPointUpdateView, ReadPointDeleteView, LocationListView, 
    LocationCreateView, LocationUpdateView, LocationDeleteView
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('readers/', reader_list, name='reader_list'),
    path('create/', reader_create, name='reader_create'),
    path('update/<int:pk>/', reader_update, name='reader_update'),
    path('delete/<int:pk>/', reader_delete, name='reader_delete'),
    path('start-preset/<int:pk>/', start_preset, name='start_preset'),
    path('stop-preset/<int:pk>/', stop_preset, name='stop_preset'),
    path('webhook/', webhook_receiver, name='webhook_receiver'),
    path('tags/', tag_event_list, name='tag_event_list'),
    path('tag-event/<int:event_id>/details/', tag_event_details, name='tag_event_details'),
    path('tags/export/', export_tag_events, name='export_tag_events'),
    path('reader/<int:reader_id>/presets/', PresetListView.as_view(), name='preset_list'),
    path('reader/<int:reader_id>/presets/add/', PresetCreateView.as_view(), name='preset_add'),
    path('preset/<int:pk>/edit/', PresetUpdateView.as_view(), name='preset_edit'),
    path('preset/<int:pk>/delete/', PresetDeleteView.as_view(), name='preset_delete'),
    path('get-preset-details/<int:reader_id>/<str:preset_id>/', get_preset_details, name='get_preset_details'),
    path('query-presets/<int:pk>/', query_presets, name='query_presets'),
    path('preset-templates/', PresetTemplateListView.as_view(), name='preset_template_list'),
    path('preset-templates/add/', PresetTemplateCreateView.as_view(), name='preset_template_add'),
    path('preset-templates/<int:pk>/edit/', PresetTemplateUpdateView.as_view(), name='preset_template_edit'),
    path('preset-templates/<int:pk>/delete/', PresetTemplateDeleteView.as_view(), name='preset_template_delete'),
    path('webhook-templates/', WebhookTemplateListView.as_view(), name='webhook_template_list'),
    path('webhook-templates/add/', WebhookTemplateCreateView.as_view(), name='webhook_template_add'),
    path('webhook-templates/<int:pk>/edit/', WebhookTemplateUpdateView.as_view(), name='webhook_template_edit'),
    path('webhook-templates/<int:pk>/delete/', WebhookTemplateDeleteView.as_view(), name='webhook_template_delete'),
    path('mqtt-templates/', MqttTemplateListView.as_view(), name='mqtt_template_list'),
    path('mqtt-templates/add/', MqttTemplateCreateView.as_view(), name='mqtt_template_add'),
    path('mqtt-templates/<int:pk>/edit/', MqttTemplateUpdateView.as_view(), name='mqtt_template_edit'),
    path('mqtt-templates/<int:pk>/delete/', MqttTemplateDeleteView.as_view(), name='mqtt_template_delete'),
    path('webhook-template-results/', WebhookTemplateResultListView.as_view(), name='webhook_template_result_list'),
    path('webhook-template-results/<int:pk>/retry/', WebhookTemplateResultRetryView.as_view(), name='webhook_template_result_retry'),
    path('mqtt-template-results/', MQTTTemplateResultListView.as_view(), name='mqtt_template_result_list'),
    path('mqtt-template-results/<int:pk>/retry/', MQTTTemplateResultRetryView.as_view(), name='mqtt_template_result_retry'),
    path('logs/', view_logs, name='view_logs'),

    # TagTraceability
    path('traceability/', TagTraceabilityListView.as_view(), name='tag_traceability_list'),

    # ReadPoint
    path('read-points/', ReadPointListView.as_view(), name='read_point_list'),
    path('read-points/create/', ReadPointCreateView.as_view(), name='read_point_create'),
    path('read-points/<int:pk>/edit/', ReadPointUpdateView.as_view(), name='read_point_edit'),
    path('read-points/<int:pk>/delete/', ReadPointDeleteView.as_view(), name='read_point_delete'),

    # Location
    path('locations/', LocationListView.as_view(), name='location_list'),
    path('locations/create/', LocationCreateView.as_view(), name='location_create'),
    path('locations/<int:pk>/edit/', LocationUpdateView.as_view(), name='location_edit'),
    path('locations/<int:pk>/delete/', LocationDeleteView.as_view(), name='location_delete'),
    
]
