from rest_framework import serializers
from .models import Servo

class ServoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servo
        fields = ['angle']
        extra_kwargs = {
            'angle': {
                'min_value': 0,
                'max_value': 180,  # Fuerza validación de rango
                'error_messages': {
                    'min_value': 'El ángulo mínimo es 0°',
                    'max_value': 'El ángulo máximo es 180°'
                }
            }
        }