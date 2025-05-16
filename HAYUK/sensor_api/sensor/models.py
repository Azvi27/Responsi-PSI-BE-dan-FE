from django.db import models

class PowerSystem(models.Model):
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField()
    status = models.BooleanField()
    # Kolom baru
    voltage = models.FloatField(default=0)
    vibration = models.BooleanField(default=True)  # True = aman, False = tidak aman
    current = models.FloatField(default=0)
    power_consumption = models.FloatField(default=0)

    def __str__(self):
        return f"PowerSystem {self.id}"

    class Meta:
        db_table = 'sensor_powersystem'
        managed = False

class SensorData(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    mass = models.FloatField()
    brightness = models.FloatField()
    good_product = models.IntegerField()
    bad_product = models.IntegerField()
    
    # Kami tidak perlu lagi menambahkan foreign key ke PowerSystem
    # karena struktur telah berubah
    
    def __str__(self):
        return f"SensorData {self.id}"

    class Meta:
        db_table = 'sensor_sensordata'
        managed = False