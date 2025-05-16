from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse
import requests
import logging
from .models import PowerSystem, SensorData
from .serializers import PowerSystemSerializer, SensorDataSerializer, PowerCommandSerializer

# URL dan timeout Raspberry Pi
RASPBERRY_PI_URL = "http://192.168.91.187:5000"
POWER_CONTROL_URL = f"{RASPBERRY_PI_URL}/control-power"
RESET_COUNTER_URL = f"{RASPBERRY_PI_URL}/reset-counter"  # URL untuk reset counter di Raspberry Pi
TIMEOUT = 5

# Viewsets untuk administrasi - tidak perlu diubah
class PowerSystemViewSet(viewsets.ModelViewSet):
    queryset = PowerSystem.objects.all()
    serializer_class = PowerSystemSerializer

class SensorDataViewSet(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer

# Dashboard - tidak perlu diubah
def monitoring_dashboard(request):
    context = {
        "sensor": SensorData.objects.last(),
        "power": PowerSystem.objects.last(),
    }
    return render(request, 'monitoring/dashboard.html', context)

# API untuk data sensor dan power - diperbarui untuk struktur baru
@api_view(['POST'])
def create_data(request, data_type):
    if data_type == 'sensor':
        # Ekstrak dan persiapkan data untuk SensorData
        sensor_data = {
            'timestamp': request.data.get('timestamp', timezone.now()),
            'mass': request.data.get('mass', 0),
            'brightness': request.data.get('brightness', 0),
            'good_product': request.data.get('good_product', 0),
            'bad_product': request.data.get('bad_product', 0)
        }
        
        # Kalkulasi nilai good_product dan bad_product jika nilai = 1
        latest_data = SensorData.objects.order_by('-timestamp').first()
        if latest_data:
            if int(request.data.get('good_product', 0)) == 1:
                sensor_data['good_product'] = latest_data.good_product + 1
            if int(request.data.get('bad_product', 0)) == 1:
                sensor_data['bad_product'] = latest_data.bad_product + 1
        
        sensor_serializer = SensorDataSerializer(data=sensor_data)
        
        # Persiapkan data untuk PowerSystem
        power_data = {
            'timestamp': request.data.get('timestamp', timezone.now()),
            'status': request.data.get('status', True),
            'voltage': request.data.get('voltage', 0),
            'current': request.data.get('current', 0),
            'power_consumption': request.data.get('power_consumption', 0),
        }
        
        # Handle vibration status
        if 'vibration_level' in request.data:
            vibration_level = float(request.data.get('vibration_level', 0))
            power_data['vibration'] = vibration_level < 5  # True jika aman, False jika tidak
        
        power_serializer = PowerSystemSerializer(data=power_data)
        
        # Validasi dan simpan data
        if sensor_serializer.is_valid() and power_serializer.is_valid():
            sensor_serializer.save()
            power_serializer.save()
            return Response({
                "message": "Sensor data saved successfully",
                "sensor": sensor_serializer.data,
                "power": power_serializer.data
            }, status=status.HTTP_201_CREATED)
        
        # Jika terjadi error, berikan detail error
        errors = {}
        if not sensor_serializer.is_valid():
            errors['sensor'] = sensor_serializer.errors
        if not power_serializer.is_valid():
            errors['power'] = power_serializer.errors
        
        return Response({"errors": errors}, status=status.HTTP_400_BAD_REQUEST)
    
    else:  # power
        # Langsung gunakan PowerSystemSerializer
        serializer = PowerSystemSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Power system status saved successfully", "data": serializer.data}, 
                           status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API untuk mengirim perintah ke Raspberry Pi - masih sama
class PowerCommandView(APIView):
    def post(self, request):
        serializer = PowerCommandSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        status_value = serializer.validated_data['status']
        
        try:
            # Kirim perintah ke Raspberry Pi
            response = requests.post(
                POWER_CONTROL_URL,
                json={"status": status_value},
                timeout=TIMEOUT
            )
            
            # Jika berhasil, simpan status
            if response.status_code == 200:
                PowerSystem.objects.create(
                    timestamp=timezone.now(),
                    status=bool(status_value),
                    voltage=0,  # Default nilai untuk kolom baru
                    vibration=True,  # Default aman
                    current=0,
                    power_consumption=0
                )
                return Response({"message": "Power command sent successfully"}, 
                               status=status.HTTP_200_OK)
            else:
                return Response(
                    {"error": f"Failed to send command: {response.text}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {"error": f"Communication error: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# API untuk mendapatkan data terbaru - diperbarui untuk struktur baru
def latest_data(request):
    try:
        sensor = SensorData.objects.latest('timestamp')
        power = PowerSystem.objects.latest('timestamp')
        
        data = {
            "sensor": {
                "id": sensor.id,
                "mass": sensor.mass,
                "brightness": sensor.brightness,
                "good_product": sensor.good_product,
                "bad_product": sensor.bad_product,
                "timestamp": sensor.timestamp.isoformat(),
            },
            "power": {
                "id": power.id,
                "status": power.status,
                "voltage": power.voltage,
                "vibration": power.vibration,  # Boolean: True = aman, False = tidak aman
                "current": power.current,
                "power_consumption": power.power_consumption,
                "timestamp": power.timestamp.isoformat()
            }
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# API untuk reset counter - diperbarui untuk struktur baru
@api_view(['POST'])
def reset_count(request):
    try:
        latest = SensorData.objects.last()
        if not latest:
            return Response({"error": "No sensor data available"}, 
                           status=status.HTTP_404_NOT_FOUND)
        
        # Buat instance baru dengan counter reset di database
        SensorData.objects.create(
            timestamp=timezone.now(),
            mass=latest.mass,
            brightness=latest.brightness,
            good_product=0,  # Reset
            bad_product=0    # Reset
        )
        
        # Tambahan kode untuk reset counter di Raspberry Pi
        try:
            # Kirim perintah reset ke Raspberry Pi
            pi_response = requests.post(
                RESET_COUNTER_URL,
                json={"reset": True},
                timeout=TIMEOUT
            )
            
            if pi_response.status_code != 200:
                return Response(
                    {"warning": "Counters reset in database but failed to reset on Raspberry Pi"}, 
                    status=status.HTTP_200_OK
                )
                
        except Exception as e:
            return Response(
                {"warning": f"Counters reset in database but failed to communicate with Raspberry Pi: {str(e)}"}, 
                status=status.HTTP_200_OK
            )
        
        return Response({"message": "Counters reset successfully on database and Raspberry Pi"}, 
                       status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, 
                       status=status.HTTP_500_INTERNAL_SERVER_ERROR)