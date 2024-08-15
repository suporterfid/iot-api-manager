from django.urls import path
from . import views
from .views import reader_list, reader_create, reader_update, reader_delete, start_preset, stop_preset, webhook_receiver, tag_event_list

urlpatterns = [
    path('', reader_list, name='reader_list'),
    path('create/', reader_create, name='reader_create'),
    path('update/<int:pk>/', reader_update, name='reader_update'),
    path('delete/<int:pk>/', reader_delete, name='reader_delete'),
    path('start-preset/<int:pk>/', start_preset, name='start_preset'),
    path('stop-preset/<int:pk>/', stop_preset, name='stop_preset'),
    path('webhook/', webhook_receiver, name='webhook_receiver'),
    path('tags/', tag_event_list, name='tag_event_list'),
    path('tag-event/<int:event_id>/details/', views.tag_event_details, name='tag_event_details'),
]
