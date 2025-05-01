from rest_framework import serializers
from .models import Reporte, Asignacion, InformeMantenimiento

class ReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = '__all__'

class AsignacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asignacion
        fields = '__all__'

class InformeMantenimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InformeMantenimiento
        fields = '__all__'