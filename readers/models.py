from django.db import models
import requests

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
