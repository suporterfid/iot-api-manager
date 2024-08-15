from django.db import models

class Reader(models.Model):
    serial_number = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    ip_address = models.GenericIPAddressField()
    port = models.IntegerField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    preset_id = models.CharField(max_length=100, default='default')

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
