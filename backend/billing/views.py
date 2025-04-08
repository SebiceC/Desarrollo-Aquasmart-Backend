from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from .rates.models import TaxRate, ConsumptionRate
from .company.models import Company
from .rates.serializers import TaxRateSerializer, ConsumptionRateSerializer
from .company.serializers import CompanySerializer

class RatesAndCompanyView(APIView):
    @transaction.atomic # Si se produce un error, se revertirán todos los cambios en la base de datos
    def patch(self, request):
        try:
            response_data = {}
            has_changes = False
            # --- Validar existencia de la empresa ---
            company = Company.objects.first()  # Asume una sola company

            # --- Validar existencia de la empresa ---
            if not company:
                transaction.set_rollback(True)
                return Response(
                    {"error": "No hay empresa registrada."},
                    status=status.HTTP_404_NOT_FOUND
                )

            if 'company' in request.data:
                company_serializer = CompanySerializer(
                    company, 
                    data=request.data['company'], 
                    partial=True  # <-- Habilitar actualización parcial
                )
                if not company_serializer.is_valid():
                    transaction.set_rollback(True)
                    return Response(company_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                if company_serializer.has_changes():
                    company_serializer.save()
                    response_data['company'] = company_serializer.data
                    has_changes = True

            # --- Actualizar tarifas de impuestos ---
            if 'tax_rates' in request.data:
                tax_rates_data = request.data['tax_rates']
                updated_tax_rates = []
                for tax_data in tax_rates_data:
                    try:
                        instance = TaxRate.objects.get(tax_type=tax_data['tax_type'])
                    except ObjectDoesNotExist:
                        transaction.set_rollback(True)
                        return Response(
                            {"error": f"Tarifa de impuesto '{tax_data['tax_type']}' no existe."},
                            status=status.HTTP_404_NOT_FOUND
                        )
                    serializer = TaxRateSerializer(
                        instance, 
                        data=tax_data, 
                        partial=True  # <-- Actualización parcial
                    )
                    if not serializer.is_valid():
                        transaction.set_rollback(True)
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                    if serializer.has_changes():
                        serializer.save()
                        updated_tax_rates.append(serializer.data)
                        has_changes = True

                if updated_tax_rates:
                    response_data['tax_rates'] = updated_tax_rates
            
            # --- Actualizar tarifas de consumo ---
            if 'consumption_rates' in request.data:
                consumption_rates_data = request.data['consumption_rates']
                updated_consumption_rates = []
                for consumption_data in consumption_rates_data:
                    try:
                        instance = ConsumptionRate.objects.get(crop_type=consumption_data['crop_type'])
                    except ObjectDoesNotExist:
                        transaction.set_rollback(True)
                        return Response(
                            {"error": f"Tipo de cultivo '{consumption_data['crop_type']}' no existe."},
                            status=status.HTTP_404_NOT_FOUND
                        )
                    serializer = ConsumptionRateSerializer(
                        instance, 
                        data=consumption_data, 
                        partial=True  # <-- Actualización parcial
                    )
                    if not serializer.is_valid():
                        transaction.set_rollback(True)
                        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                    if serializer.has_changes():
                        serializer.save()
                        updated_consumption_rates.append(serializer.data)
                        has_changes = True
                
                if updated_consumption_rates:
                    response_data['consumption_rates'] = updated_consumption_rates


            if not has_changes:
                return Response(
                    {"error": "Formulario sin cambios. No se realizó ningún cambio en la información."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            return Response(response_data, status=status.HTTP_200_OK)

        except KeyError as e:
            transaction.set_rollback(True)
            return Response(
                {"error": f"Campo faltante: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            transaction.set_rollback(True)
            return Response(
                {"error": f"Error interno: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def get(self, request):
        try:
            company = Company.objects.first()
            tax_rates = TaxRate.objects.all()
            consumption_rates = ConsumptionRate.objects.all()

            # Serializar datos
            company_serializer = CompanySerializer(company)
            tax_rates_serializer = TaxRateSerializer(tax_rates, many=True)
            consumption_rates_serializer = ConsumptionRateSerializer(consumption_rates, many=True)

            return Response({
                "company": company_serializer.data,
                "tax_rates": tax_rates_serializer.data,
                "consumption_rates": consumption_rates_serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )