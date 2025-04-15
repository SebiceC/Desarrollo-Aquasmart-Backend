from rest_framework import serializers
from .models import Company
from billing.serializers import HasChangesSerializer

class CompanySerializer(HasChangesSerializer):
    class Meta:
        model = Company
        fields = '__all__'
        extra_kwargs = {
            'name': {'required': False},
            'nit': {'required': False},
            'address': {'required': False},
            'phone': {'required': False},
            'email': {'required': False},
        }
    
    def validate_name(self, value):
        """Validar que el nombre tenga entre 1 y 60 caracteres"""
        if len(value) < 1 or len(value) > 60:
            raise serializers.ValidationError("El nombre debe tener entre 1 y 60 caracteres.")
        return value
    
    def validate_nit(self, value):
        """Validar que el NIT tenga entre 1 y 11 caracteres"""
        if len(value) < 1 or len(value) > 11:
            raise serializers.ValidationError("El NIT debe tener entre 1 y 11 caracteres.")
        return value
    
    def validate_address(self, value):
        """Validar que la dirección tenga entre 1 y 35 caracteres"""
        if len(value) < 1 or len(value) > 35:
            raise serializers.ValidationError("La dirección debe tener entre 1 y 35 caracteres.")
        return value
    
    def validate_phone(self, value):
        """Validar que el teléfono tenga 10 caracteres"""
        if len(value) != 10:
            raise serializers.ValidationError("El teléfono debe tener 10 caracteres.")
        return value
    
    def validate_email(self, value):
        """Validar que el correo electrónico tenga entre 1 y 50 caracteres"""
        if len(value) < 1 or len(value) > 50:
            raise serializers.ValidationError("El correo electrónico debe tener entre 1 y 50 caracteres.")
        return value