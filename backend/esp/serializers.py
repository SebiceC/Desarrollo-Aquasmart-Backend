from rest_framework import serializers
from .models import Consumo

class ConsumoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consumo
        fields = '__all__'