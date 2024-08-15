from django.contrib import admin
from django.contrib.admin import AdminSite
from .models import Reader, TagEvent

class MyAdminSite(AdminSite):
    site_header = 'Reader Manager Admin'
    site_title = 'Reader Manager Admin Portal'
    index_title = 'Welcome to Reader Manager Admin'

admin_site = MyAdminSite(name='myadmin')

@admin.register(Reader)
class ReaderAdmin(admin.ModelAdmin):
    list_display = ('name', 'serial_number', 'ip_address', 'port')
    search_fields = ('name', 'serial_number', 'ip_address')
    list_filter = ('ip_address',)
    ordering = ('name',)

@admin.register(TagEvent)
class TagEventAdmin(admin.ModelAdmin):
    list_display = ('reader', 'epc', 'timestamp')
    search_fields = ('epc',)
    list_filter = ('reader', 'timestamp')
    ordering = ('-timestamp',)
