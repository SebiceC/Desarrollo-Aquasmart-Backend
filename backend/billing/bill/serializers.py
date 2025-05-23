from rest_framework import serializers
from .models import Bill,STATUS_CHOICES
from billing.rates.models import FixedConsumptionRate, VolumetricConsumptionRate
from plots_lots.models import CropType

# Serializer del modelo de Factura (Bill)
class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        fields = '__all__'
        read_only_fields = [
            'id_bill', 'code', 'total_fixed_rate', 'total_volumetric_rate', 'total_amount',
            'pdf_bill_name', 'creation_date', 'due_payment_date',#FALTABA UNA COMA
            'company_name', 'company_nit', 'company_address', 'company_phone', 'company_email',
            'client', 'client_name', 'client_document', 'client_address',
            'lot_code', 'plot_name',
            'fixed_consumption_rate', 'fixed_rate_code', 'fixed_rate_name', 'fixed_rate_value',
            'volumetric_consumption_rate','volumetric_rate_code', 'volumetric_rate_name', 'volumetric_rate_value']
        extra_kwargs = {
            'code': {'error_messages': {'unique': "Ya existe una factura con este código."}},
            'cufe': {'error_messages': {'unique': "Ya existe una factura con este CUFE."}},
            'step_number': {'error_messages': {'unique': "Ya existe una factura con este número de paso."}},
        }

    def create(self, validated_data):
        # Obtener instancias relacionadas
        company = validated_data['company']
        client = validated_data['client']
        lot = validated_data['lot']
        fixed_rate = validated_data['fixed_consumption_rate']
        volumetric_rate = validated_data['volumetric_consumption_rate']

        # Poblar campos desnormalizados
        validated_data['company_name'] = company.name
        validated_data['company_nit'] = company.nit
        validated_data['company_address'] = company.address
        validated_data['company_phone'] = company.phone
        validated_data['company_email'] = company.email

        validated_data['client_name'] = client.get_full_name()
        validated_data['client_document'] = client.document
        validated_data['client_address'] = client.address

        validated_data['lot_code'] = lot.id_lot
        validated_data['plot_name'] = lot.plot.plot_name

        validated_data['fixed_rate_code'] = fixed_rate.code
        validated_data['fixed_rate__name'] = f"{fixed_rate._meta.verbose_name} {fixed_rate.crop_type.name}"
        validated_data['fixed_rate_value'] = fixed_rate.fixed_rate_cents / 100

        validated_data['volumetric_rate_code'] = volumetric_rate.code
        validated_data['volumetric_rate_name'] = f"{volumetric_rate._meta.verbose_name} {volumetric_rate.crop_type.name}"
        validated_data['volumetric_rate_value'] = volumetric_rate.volumetric_rate_cents / 100

        # Calcular totales automáticamente
        fixed_rate_quantity = validated_data.get('fixed_rate_quantity', 0)
        volumetric_rate_quantity = validated_data.get('volumetric_rate_quantity', 0)
        fixed_rate_value = validated_data['fixed_rate_value']
        volumetric_rate_value = validated_data['volumetric_rate_value']

        total_fixed_rate = fixed_rate_value * fixed_rate_quantity
        total_volumetric_rate = volumetric_rate_value * volumetric_rate_quantity
        total_amount = total_fixed_rate + total_volumetric_rate

        validated_data['total_fixed_rate'] = total_fixed_rate
        validated_data['total_volumetric_rate'] = total_volumetric_rate
        validated_data['total_amount'] = total_amount

        # Crear el nombre del PDF de la factura
        if 'code' in validated_data:
            validated_data['pdf_bill_name'] = f"{validated_data['code'][:2]}_{validated_data['code'][2:]}"

        return super().create(validated_data)

    def validate(self, attrs):
        # La fecha de validación de la DIAN sea superior a la de la creación de la factura
        creation = attrs.get('creation_date')
        dian_validation = attrs.get('dian_validation_date')
        if creation and dian_validation and dian_validation <= creation:
            raise serializers.ValidationError("La fecha de validación de la DIAN debe ser posterior a la de creación de la factura.")
        return attrs

class BillStatusUpdateSerializer(serializers.Serializer):
    code = serializers.CharField()
    status = serializers.ChoiceField(choices=[('pagada', dict(STATUS_CHOICES)['pagada'])])

    def validate(self, data):
        if data['status'] != 'pagada':
            raise serializers.ValidationError("Solo se permite cambiar el estado a 'pagada'.")
        return data    