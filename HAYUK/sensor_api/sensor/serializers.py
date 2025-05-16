from rest_framework import serializers
from .models import PowerSystem, SensorData
from django.utils import timezone

class PowerSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PowerSystem
        fields = ['id', 'timestamp', 'status', 'voltage', 'vibration', 'current', 'power_consumption']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # Pastikan timestamp selalu ada
        if 'timestamp' not in validated_data:
            validated_data['timestamp'] = timezone.now()
        
        # Jika ada vibration_level, tentukan status vibration berdasarkan nilai getaran
        if 'vibration_level' in self.initial_data:
            vibration_level = float(self.initial_data['vibration_level'])
            # Konversi langsung ke boolean - True jika aman, False jika tidak
            validated_data['vibration'] = vibration_level < 5
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Update timestamp saat update
        validated_data['timestamp'] = timezone.now()
        
        
        # Jika ada vibration_level, tentukan status vibration berdasarkan nilai getaran
        if 'vibration_level' in self.initial_data:
            vibration_level = float(self.initial_data['vibration_level'])
            validated_data['vibration'] = vibration_level < 5
        
        return super().update(instance, validated_data)

class SensorDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SensorData
        fields = ['id', 'timestamp', 'mass', 'brightness', 'good_product', 'bad_product']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        # Pastikan timestamp selalu ada
        if 'timestamp' not in validated_data:
            validated_data['timestamp'] = timezone.now()
        
        return super().create(validated_data)

# Serializer untuk Power Command tetap sama
class PowerCommandSerializer(serializers.Serializer):
    status = serializers.IntegerField()