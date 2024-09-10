from django.test import TestCase
from .models import Reader, TagEvent

class ReaderModelTest(TestCase):

    def setUp(self):
        self.reader = Reader.objects.create(
            serial_number="123-ABC-456",
            name="Test Reader",
            ip_address="192.168.1.1",
            port=8080,
            username="admin",
            password="password"
        )

    def test_reader_creation(self):
        self.assertEqual(self.reader.name, "Test Reader")
        self.assertEqual(self.reader.serial_number, "123-ABC-456")
        self.assertEqual(self.reader.ip_address, "192.168.1.1")
        self.assertEqual(self.reader.port, 8080)
        self.assertEqual(self.reader.username, "admin")
        self.assertEqual(self.reader.password, "password")

class TagEventModelTest(TestCase):

    def setUp(self):
        self.reader = Reader.objects.create(
            serial_number="123-ABC-456",
            name="Test Reader",
            ip_address="192.168.1.1",
            port=8080,
            username="admin",
            password="password"
        )
        self.tag_event = TagEvent.objects.create(
            reader=self.reader,
            epc="E2003412012345678900",
            timestamp="2024-08-09T17:44:30.659Z"
        )

    def test_tag_event_creation(self):
        self.assertEqual(self.tag_event.reader.name, "Test Reader")
        self.assertEqual(self.tag_event.epc, "E2003412012345678900")
        self.assertEqual(self.tag_event.timestamp.isoformat(), "2024-08-09T17:44:30.659000+00:00")
