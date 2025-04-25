from django.db import models

class PowerSystem(models.Model):
    id = models.BigAutoField(primary_key=True)
    timestamp = models.DateTimeField()
    status = models.BooleanField()
    reason = models.CharField(max_length=50)

    def __str__(self):
        return f"PowerSystem {self.id}"

    class Meta:
        db_table = 'sensor_powersystem'
        managed = False

class SensorData(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField()
    vibration_level = models.FloatField()
    motor_voltage = models.FloatField()
    motor_current = models.FloatField()
    power_consumption = models.FloatField()
    bottle_mass = models.FloatField()
    bottle_brightness = models.FloatField()
    good_product = models.IntegerField()
    bad_product = models.IntegerField()
    power_system = models.ForeignKey(
        PowerSystem,
        on_delete=models.CASCADE,
        db_column='power_system_id'
    )

    def __str__(self):
        return f"SensorData {self.id}"

    class Meta:
        db_table = 'sensor_sensordata'
        managed = False
