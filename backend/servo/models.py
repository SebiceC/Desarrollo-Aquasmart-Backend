from django.db import models

class Servo(models.Model):
    angle = models.IntegerField(default=0)  # Rango 0-180°
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Posición: {self.angle}°"