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