# serializers.py
from rest_framework import serializers
from .models import SmartReader

class SmartReaderSerializer(serializers.ModelSerializer):
    class Meta:
        model = SmartReader
        fields = '__all__'
