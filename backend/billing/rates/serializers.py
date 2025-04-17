from rest_framework import serializers
from .models import TaxRate, FixedConsumptionRate, VolumetricConsumptionRate
from billing.serializers import HasChangesSerializer

class TaxRateSerializer(HasChangesSerializer):
    class Meta:
        model = TaxRate
        fields = '__all__'
        extra_kwargs = {
            'tax_type': {'required': False},
            'tax_value': {'required': False}
        }

    def validate_tax_value(self, value):
        """
        Valida que el valor del impuesto esté entre 0 y 100.
        """
        if value < 0 or value > 100:
            raise serializers.ValidationError("El valor del impuesto debe estar entre 0 y 100.")
        return value

class FixedConsumptionRateSerializer(HasChangesSerializer):
    fixed_rate = serializers.SerializerMethodField()

    class Meta:
        model = FixedConsumptionRate
        fields = '__all__'

    def get_fixed_rate(self, obj):
        return obj.fixed_rate_cents / 100

    def to_internal_value(self, data):
        data = data.copy()
        if 'fixed_rate' in data:
            data['fixed_rate_cents'] = int(float(data.pop('fixed_rate')) * 100)
        return super().to_internal_value(data)

class VolumetricConsumptionRateSerializer(HasChangesSerializer):
    volumetric_rate = serializers.SerializerMethodField()

    class Meta:
        model = VolumetricConsumptionRate
        fields = '__all__'

    def get_volumetric_rate(self, obj):
        return obj.volumetric_rate_cents / 100

    def to_internal_value(self, data):
        data = data.copy()
        if 'volumetric_rate' in data:
            data['volumetric_rate_cents'] = int(float(data.pop('volumetric_rate')) * 100)
        return super().to_internal_value(data)

# class ConsumptionRateSerializer(HasChangesSerializer):
#     fixed_rate = serializers.DecimalField(
#         max_digits=10, 
#         decimal_places=2, 
#         write_only=True,
#         source="fixed_rate_cents")
#     volumetric_rate = serializers.DecimalField(
#         max_digits=10, 
#         decimal_places=2, 
#         write_only=True,
#         source="volumetric_rate_cents"
#     )
    
#     class Meta:
#         model = ConsumptionRate
#         fields = '__all__'
#         extra_kwargs = {
#             'crop_type': {'required': False},
#             'fixed_rate_cents': {'required': False},
#             'volumetric_rate_cents': {'required': False}
#         }
    
#     def to_representation(self, instance):
#         data = super().to_representation(instance)
#         # Mostrar valores en pesos
#         data['fixed_rate'] = instance.fixed_rate_cents / 100
#         data['volumetric_rate'] = instance.volumetric_rate_cents / 100
#         return data
    
#     def to_internal_value(self, data):
#         # Convertir valores a COP al guardar
#         data = data.copy()
#         if 'fixed_rate' in data:
#             data['fixed_rate_cents'] = int(float(data.pop('fixed_rate')) * 100)
#         if 'volumetric_rate' in data:
#             data['volumetric_rate_cents'] = int(float(data.pop('volumetric_rate')) * 100)
#         return super().to_internal_value(data)