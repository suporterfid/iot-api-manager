from django import forms
from .models import Reader, Preset, PresetTemplate, WebhookTemplate, MqttTemplate

class ReaderForm(forms.ModelForm):
    class Meta:
        model = Reader
        fields = ['serial_number', 'name', 'ip_address', 'port', 'username', 'password']

class PresetForm(forms.ModelForm):
    class Meta:
        model = Preset
        fields = ['preset_id', 'configuration', 'is_active']
        widgets = {
            'configuration': forms.Textarea(attrs={'rows': 10, 'cols': 40}),
        }

    def __init__(self, *args, **kwargs):
        super(PresetForm, self).__init__(*args, **kwargs)
        self.fields['is_active'].widget.attrs.update({'class': 'form-check-input'})

    def clean_is_active(self):
        is_active = self.cleaned_data.get('is_active')
        if is_active:
            # Ensure only one active preset per reader
            reader = self.instance.reader
            Preset.objects.filter(reader=reader).update(is_active=False)
        return is_active

class PresetTemplateForm(forms.ModelForm):
    class Meta:
        model = PresetTemplate
        fields = ['name', 'configuration', 'readers']
        widgets = {
            'configuration': forms.Textarea(attrs={'rows': 10, 'cols': 80}),
            'readers': forms.CheckboxSelectMultiple(),
        }

class WebhookTemplateForm(forms.ModelForm):
    class Meta:
        model = WebhookTemplate
        fields = ['name', 'content', 'readers']
        widgets = {
            'content': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }

class MqttTemplateForm(forms.ModelForm):
    class Meta:
        model = MqttTemplate
        fields = ['name', 'content', 'readers']
        widgets = {
            'content': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }
