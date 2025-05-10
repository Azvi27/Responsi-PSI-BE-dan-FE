from rest_framework import serializers
from .models import PowerSystem, SensorData
from django.utils import timezone

class PowerSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerSystem
        fields = ['id', 'timestamp', 'status', 'reason']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # Pastikan timestamp selalu ada
        if 'timestamp' not in validated_data:
            validated_data['timestamp'] = timezone.now()
        
        # Set reason berdasarkan status
        if 'reason' not in validated_data:
            validated_data['reason'] = 'Manual activation' if validated_data.get('status', False) else 'Manual deactivation'
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Update timestamp saat update
        validated_data['timestamp'] = timezone.now()
        
        # Update reason berdasarkan status baru
        if 'status' in validated_data and 'reason' not in validated_data:
            validated_data['reason'] = 'Manual activation' if validated_data['status'] else 'Manual deactivation'
        
        return super().update(instance, validated_data)


class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ['id', 'timestamp', 'vibration_level', 'motor_voltage', 'motor_current', 
                 'power_consumption', 'bottle_mass', 'bottle_brightness', 
                 'good_product', 'bad_product', 'power_system']
        read_only_fields = ['id']

from rest_framework import serializers

class PowerCommandSerializer(serializers.Serializer):
    status = serializers.IntegerField()
