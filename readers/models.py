from django.db import models
import requests
from django.utils import timezone

class Reader(models.Model):
    serial_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    active_preset = models.OneToOneField('Preset', on_delete=models.SET_NULL, null=True, blank=True, related_name='active_reader')

    def __str__(self):
        return self.name
    
    def get_active_preset_from_status(self):
        url = f"https://{self.ip_address}:{self.port}/api/v1/status"
        auth = (self.username, self.password)
        try:
            response = requests.get(url, auth=auth, headers={'Content-Type': 'application/json'}, verify=False)
            response.raise_for_status()
            status_data = response.json()
            active_preset_id = status_data.get("activePreset", {}).get("id", "No Active Preset")
            return active_preset_id
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"

class Location(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ReadPoint(models.Model):
    name = models.CharField(max_length=100)
    readers = models.ManyToManyField(Reader, related_name='read_points', blank=True)
    timeout_seconds = models.IntegerField(default=300)  # Timeout in seconds

    def __str__(self):
        return self.name

class TagTraceability(models.Model):
    epc = models.CharField(max_length=256)
    read_point = models.ForeignKey(ReadPoint, on_delete=models.CASCADE)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    arrived_at = models.DateTimeField(null=True, blank=True)
    last_seen = models.DateTimeField(null=True, blank=True)
    departed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'{self.epc} - {self.read_point.name}'

    def update_departure(self):
        if not self.departed_at:
            self.departed_at = timezone.now()
            self.save()
        
class WebhookTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True)
    content = models.JSONField(default=dict)  # Single JSON field for the entire template content
    readers = models.ManyToManyField('Reader', related_name='webhook_templates')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Enqueue a task to send the template to each associated reader
        from .tasks import process_webhook_settings
        for reader in self.readers.all():
            process_webhook_settings.apply_async((self.id, reader.id))

    def __str__(self):
        return self.name

class WebhookTemplateApplicationResult(models.Model):
    template = models.ForeignKey(WebhookTemplate, on_delete=models.CASCADE, related_name='application_results')
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name='webhook_application_results')
    success = models.BooleanField(default=False)
    response_message = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    retry = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.template.name} -> {self.reader.name} ({self.success})'


class MqttTemplate(models.Model):
    name = models.CharField(max_length=255)
    content = models.JSONField(default=dict)
    readers = models.ManyToManyField(Reader, related_name='mqtt_templates')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Enqueue a task to send the template to each associated reader
        from .tasks import process_mqtt_settings
        for reader in self.readers.all():
            process_mqtt_settings.apply_async((self.id, reader.id))

    def __str__(self):
        return self.name

class MQTTTemplateApplicationResult(models.Model):
    template = models.ForeignKey(MqttTemplate, on_delete=models.CASCADE, related_name='application_results')
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name='mqtt_application_results')
    success = models.BooleanField(default=False)
    response_message = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    retry = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.template.name} -> {self.reader.name} ({self.success})'
    
class Preset(models.Model):
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE, related_name='presets')
    preset_id = models.CharField(max_length=255, unique=True)
    configuration = models.JSONField()  # Stores the preset configuration as JSON
    is_active = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_active:
            # Deactivate all other presets for this reader
            Preset.objects.filter(reader=self.reader, is_active=True).update(is_active=False)
            self.reader.active_preset = self
            self.reader.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reader.name} - {self.preset_id}"
    
    def send_to_reader(self):
        url = f"https://{self.reader.ip_address}:{self.reader.port}/api/v1/profiles/inventory/presets/{self.preset_id}"
        auth = (self.reader.username, self.reader.password)
        headers = {'Content-Type': 'application/json'}
        response = requests.put(url, json=self.configuration, auth=auth, headers=headers, verify=False)
        return response

    def delete_from_reader(self):
        url = f"https://{self.reader.ip_address}:{self.reader.port}/api/v1/profiles/inventory/presets/{self.preset_id}"
        auth = (self.reader.username, self.reader.password)
        response = requests.delete(url, auth=auth, verify=False)
        return response
    
class PresetTemplate(models.Model):
    name = models.CharField(max_length=255, unique=True)
    configuration = models.JSONField()  # Stores the preset configuration as JSON
    readers = models.ManyToManyField('Reader', related_name='preset_templates', blank=True)

    def __str__(self):
        return self.name

class TagEvent(models.Model):
    reader = models.ForeignKey(Reader, on_delete=models.CASCADE)
    epc = models.CharField(max_length=256)
    timestamp = models.DateTimeField()
    antenna_port = models.PositiveIntegerField(null=True, blank=True)
    antenna_name = models.CharField(max_length=256, null=True, blank=True)
    peak_rssi_cdbm = models.IntegerField(null=True, blank=True)
    frequency = models.FloatField(null=True, blank=True)
    transmit_power_cdbm = models.FloatField(null=True, blank=True)
    last_seen_time = models.DateTimeField(null=True, blank=True)
    tid = models.CharField(max_length=256, null=True, blank=True)
    tid_hex = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return f'{self.reader.name} - {self.epc}'
