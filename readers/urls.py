from django.urls import path
from . import views
from .views import (
    dashboard, reader_list, reader_create, reader_update, 
    reader_delete, start_preset, stop_preset, webhook_receiver, 
    tag_event_list, tag_event_details, export_tag_events, PresetListView, PresetCreateView, 
    PresetUpdateView, PresetDeleteView, query_presets, get_preset_details
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
    
]
