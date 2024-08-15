from django import forms
from .models import Reader

class ReaderForm(forms.ModelForm):
    class Meta:
        model = Reader
        fields = ['serial_number', 'name', 'ip_address', 'port', 'username', 'password', 'preset_id']
