from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.utils import timezone
from django.shortcuts import render
from django.http import JsonResponse
import requests
from .models import PowerSystem, SensorData
from .serializers import PowerSystemSerializer, SensorDataSerializer

class PowerSystemViewSet(viewsets.ModelViewSet):
    queryset = PowerSystem.objects.all()
    serializer_class = PowerSystemSerializer

class SensorDataViewSet(viewsets.ModelViewSet):
    queryset = SensorData.objects.all()
    serializer_class = SensorDataSerializer

def monitoring_dashboard(request):
    latest_sensor = SensorData.objects.last()
    latest_power = PowerSystem.objects.last()

    context = {
        "sensor": latest_sensor,
        "power": latest_power,
    }
    return render(request, 'monitoring/dashboard.html', context)

# API untuk membuat data sensor baru
@api_view(['POST'])
def create_sensor_data(request):
    serializer = SensorDataSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Sensor data saved successfully", "data": serializer.data}, 
                       status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API untuk membuat status sistem daya baru
@api_view(['POST'])
def create_power_system(request):
    serializer = PowerSystemSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({"message": "Power system status saved successfully", "data": serializer.data}, 
                       status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PowerCommandSerializer

class PowerCommandView(APIView):
    def post(self, request):
        serializer = PowerCommandSerializer(data=request.data)
        if serializer.is_valid():
            status_value = serializer.validated_data['status']
            
            # Log informasi debug
            print(f"Received power command: status={status_value}")
            
            # Logika untuk mengirim perintah ke Raspberry Pi
            try:
                # Alamat IP Raspberry Pi dan port Flask server
                raspberry_pi_url = "http://192.168.91.187:5000/control-power"
                
                print(f"Sending request to Raspberry Pi: {raspberry_pi_url}")
                print(f"Request data: {{'status': {status_value}}}")
                
                # Kirim perintah ke Raspberry Pi
                response = requests.post(
                    raspberry_pi_url,
                    json={"status": status_value},
                    timeout=5  # Tambah timeout untuk memberikan waktu lebih
                )
                
                # Log respons
                print(f"Raspberry Pi response: {response.status_code} - {response.text}")
                
                # Cek respons dari Raspberry Pi
                if response.status_code == 200:
                    # Simpan status ke database
                    power_system = PowerSystem.objects.create(
                        timestamp=timezone.now(),
                        status=bool(status_value),
                        reason="Manual activation" if status_value == 1 else "Manual deactivation"
                    )
                    
                    print(f"Created new PowerSystem record: id={power_system.id}, status={power_system.status}")
                    
                    return Response({"message": "Power command sent successfully"}, status=status.HTTP_200_OK)
                else:
                    error_msg = f"Failed to send command to Raspberry Pi: {response.text}"
                    print(error_msg)
                    return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                    
            except Exception as e:
                error_msg = f"Communication error with Raspberry Pi: {str(e)}"
                print(error_msg)
                return Response({"error": error_msg}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# API untuk mendapatkan data terbaru
def latest_data(request):
    try:
        sensor_data = SensorData.objects.latest('timestamp')
        power_status = PowerSystem.objects.latest('id')
        data = {
            "sensor": {
                "id": sensor_data.id,
                "vibration_level": sensor_data.vibration_level,
                "motor_voltage": sensor_data.motor_voltage,
                "motor_current": sensor_data.motor_current,
                "power_consumption": sensor_data.power_consumption,
                "bottle_mass": sensor_data.bottle_mass,
                "bottle_brightness": sensor_data.bottle_brightness,
                "good_product": sensor_data.good_product,
                "bad_product": sensor_data.bad_product,
            },
            "power": {
                "status": power_status.status,
                "reason": power_status.reason
            }
        }
        return JsonResponse(data)
    except (SensorData.DoesNotExist, PowerSystem.DoesNotExist) as e:
        return JsonResponse({"error": str(e)}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)

# Endpoint untuk reset counter
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