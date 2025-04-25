from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from .models import PowerSystem, SensorData
from .serializers import PowerSystemSerializer, SensorDataSerializer

class PowerSystemViewSet(viewsets.ModelViewSet):
    queryset = PowerSystem.objects.all()
    serializer_class = PowerSystemSerializer

class SensorDataViewSet(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer

from django.shortcuts import render  # Tambahkan ini di bagian atas jika belum ada

def monitoring_dashboard(request):
    from .models import SensorData, PowerSystem  # Import lokal model
    latest_sensor = SensorData.objects.last()
    latest_power = PowerSystem.objects.last()

    context = {
        "sensor": latest_sensor,
        "power": latest_power,
    }
    return render(request, 'monitoring/dashboard.html', context)

# Tambahkan endpoint untuk reset counter
@api_view(['POST'])
def reset_count(request):
    if request.method == 'POST':
        try:
            # Dapatkan data sensor terakhir
            latest_sensor = SensorData.objects.last()
            
            if latest_sensor:
                # Buat instance baru dengan nilai reset
                new_data = SensorData.objects.create(
                    timestamp=timezone.now(),
                    vibration_level=latest_sensor.vibration_level,
                    motor_voltage=latest_sensor.motor_voltage,
                    motor_current=latest_sensor.motor_current,
                    power_consumption=latest_sensor.power_consumption,
                    bottle_mass=latest_sensor.bottle_mass,
                    bottle_brightness=latest_sensor.bottle_brightness,
                    good_product=0,  # Reset ke 0
                    bad_product=0,   # Reset ke 0
                    power_system_id=latest_sensor.power_system_id
                )
                
                return Response({"success": True, "message": "Counters reset successfully"}, 
                                status=status.HTTP_200_OK)
            else:
                return Response({"success": False, "message": "No sensor data available"}, 
                                status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({"success": False, "message": str(e)}, 
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return Response({"success": False, "message": "Invalid request method"}, 
                    status=status.HTTP_400_BAD_REQUEST)