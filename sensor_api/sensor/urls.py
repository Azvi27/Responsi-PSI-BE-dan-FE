from django.urls import path, include
from rest_framework import routers
from .views import PowerSystemViewSet, SensorDataViewSet, monitoring_dashboard, reset_count

router = routers.DefaultRouter()
router.register(r'powersystem', PowerSystemViewSet)
router.register(r'sensordata', SensorDataViewSet)

urlpatterns = [
    path('', monitoring_dashboard, name='dashboard'),  
    path('api/', include(router.urls)),                 
    path('api/resetcount/', reset_count, name='reset_count'),  # Tambahkan endpoint baru
]