from rest_framework import serializers
from .models import Company
from billing.serializers import HasChangesSerializer

class CompanySerializer(HasChangesSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        extra_kwargs = {
            'nombre': {'required': False},
            'nit': {'required': False},
            'ciudad': {'required': False}
        }
    
    def validate_nombre(self, value):
        """Validar que el nombre tenga entre 1 y 60 caracteres"""
        if len(value) < 1 or len(value) > 60:
            raise serializers.ValidationError("El nombre debe tener entre 1 y 60 caracteres.")
        return value
    
    def validate_nit(self, value):
        """Validar que el NIT tenga entre 1 y 11 caracteres"""
        if len(value) < 1 or len(value) > 11:
            raise serializers.ValidationError("El NIT debe tener entre 1 y 11 caracteres.")
        return value

    def validate_ciudad(self, value):
        """Validar que la ciudad sea una cadena de texto"""
        original_city = self.initial_data.get('ciudad')
        if original_city is not None and not isinstance(original_city, str):
            raise serializers.ValidationError("La ciudad debe ser texto.")
        if len(value) < 3 or len(value) > 27: # 27 es el máximo de caracteres de una ciudad en Colombia ;)
            raise serializers.ValidationError("La ciudad debe tener entre 3 y 27 caracteres.")
        return value