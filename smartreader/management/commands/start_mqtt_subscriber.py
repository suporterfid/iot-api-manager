# smartreader/management/commands/start_mqtt_subscriber.py

from django.core.management.base import BaseCommand
from smartreader.mqtt_subscriber import start_mqtt_subscriber

class Command(BaseCommand):
    help = 'Start the MQTT Subscriber for SmartReader'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting MQTT Subscriber...'))
        start_mqtt_subscriber()
