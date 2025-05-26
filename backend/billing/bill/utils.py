from datetime import timedelta
from django.utils import timezone
from billing.validarfactura.utils import get_valid_access_token
import requests
import os
import json
def crear_validate_invoice(bill_instance):
    """
    Llama a la API externa para validar la factura y obtener datos necesarios.
    
    Args:
        bill_instance: Instancia del modelo Bill
        
    Returns:
        dict: Datos de la API o None si hay error
    """
    
    token = get_valid_access_token()
    if not token:
        print("no se pudo obtener un token válido")
        return None
    
    payload = {
        "numbering_range_id": 8,
        "reference_code":  bill_instance.code,
        "observation": "",
        "payment_form": "2",
        "payment_due_date": (bill_instance.due_payment_date.strftime("%Y-%m-%d") if bill_instance.due_payment_date else ""),
        "payment_method_code": "42",
        "billing_period": {
            "start_date": bill_instance.creation_date.strftime("%Y-%m-%d"),
            "start_time": "00:00:00",
            "end_date": (bill_instance.creation_date + timedelta(days=18)).strftime("%Y-%m-%d"),
            "end_time": "23:59:59"
        },
        "customer": {
            "identification": bill_instance.client_document,
            "dv": "",
            "company": "",
            "trade_name": "",
            "names": bill_instance.client_name,
            "address": bill_instance.client_address,
            "email": getattr(bill_instance.client, 'email', ''),
            "legal_organization_id": "2",
            "tribute_id": "21",
            "identification_document_id": "3",
            "municipality_id": "692"
        },
        "items": []
    }
    if bill_instance.fixed_consumption_rate and bill_instance.fixed_rate_quantity > 0:
        payload["items"].append({
            "code_reference": bill_instance.fixed_rate_code or "AGUA_FIJA",
            "name": bill_instance.fixed_rate_name or "Tarifa Fija de Agua",
            "quantity": float(bill_instance.fixed_rate_quantity),
            "discount_rate": 0,
            "price": float(bill_instance.fixed_rate_value),  # Convertir a centavos
            "tax_rate": "19.00",
            "unit_measure_id": 94,
            "standard_code_id": 1,
            "is_excluded": 1,
            "tribute_id": 1,
            "withholding_taxes": []
        })
    if bill_instance.volumetric_consumption_rate and bill_instance.volumetric_rate_quantity > 0:
        payload["items"].append({
            "code_reference": bill_instance.volumetric_rate_code or "AGUA_VOL",
            "name": bill_instance.volumetric_rate_name or "Tarifa Volumétrica de Agua",
            "quantity": float(bill_instance.volumetric_rate_quantity),
            "discount_rate": 0,
            "price": float(bill_instance.volumetric_rate_value),  # Convertir a centavos
            "tax_rate": "19.00",
            "unit_measure_id": 94,
            "standard_code_id": 1,
            "is_excluded": 1,
            "tribute_id": 1,
            "withholding_taxes": []
        })    
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }
    scope ="/v1/bills/validate"
    url_protegido = os.getenv("url_api_f") + scope 
    response = requests.post(url_protegido, headers=headers, json=payload)

    if response.status_code == 201:
        data = response.json()
        number = data["data"]["bill"]["number"]
        qr = data["data"]["bill"]["qr"]
        cufe = data["data"]["bill"]["cufe"]
        
        print(f"Número de factura: {number}")
        print(f"Número de factura: {qr}")
        print(f"Número de factura: {cufe}")
        print("Datos recibidos desde la API:")
        #print(json.dumps(data, indent=4))
        return data
    else:
        print(f"Error en solicitud protegida: {response.status_code} - {response.text}")
        return None

def actualizar_factura_con_api_data(bill_instance, api_data):
    """
    Actualiza una factura con los datos obtenidos de la API.
    
    Args:
        bill_instance: Instancia del modelo Bill
        api_data: Datos devueltos por crear_validate_invoice()
    """
    if not api_data:
        return False
    number = api_data["data"]["bill"]["number"]
    pdf_base64 = get_invoce_pdf(number)
    # Actualizar los campos con los datos de la API
    bill_instance.cufe = api_data["data"]["bill"]["cufe"]
    bill_instance.step_number = number
    bill_instance.qr_url = api_data["data"]["bill"]["qr"]
    bill_instance.dian_validation_date = timezone.now()
    bill_instance.pdf_base64 = pdf_base64
    bill_instance.total_amount = api_data["data"]["bill"]["total"]
    
    # Usar update para evitar recursión
    from .models import Bill  # Import local para evitar circular imports
    Bill.objects.filter(pk=bill_instance.pk).update(
        cufe=bill_instance.cufe,
        step_number=bill_instance.step_number,
        qr_url=bill_instance.qr_url,
        dian_validation_date=bill_instance.dian_validation_date,
        pdf_base64=bill_instance.pdf_base64,
        total_amount=bill_instance.total_amount
    )
    
    print(f"Factura {bill_instance.code} validada exitosamente:")
    print(f"- CUFE: {bill_instance.cufe}")
    print(f"- Número: {bill_instance.step_number}")
    print(f"- QR: {bill_instance.qr_url}")
    print(f"PDF-64:{bill_instance.pdf_base64[:20]}",)
    
    return True 

def get_invoce_pdf(number):
    
    token = get_valid_access_token()    
    if not token:
        print("no se pudo obtener un token válido")
        return None   
    
    scope ="/v1/bills/download-pdf/"
    headers = {
        'Authorization': f'Bearer {token}',
        'Accept': 'application/json'
    }

    url_protegido = os.getenv("url_api_f")+scope+number
    response = requests.get(url_protegido, headers=headers)

    if response.status_code == 200:
        data = response.json()
        #print("Datos recibidos desde la API:")
        #print("nombre factura",data["data"]["file_name"])
        pdf_base_64 = data["data"]["pdf_base_64_encoded"]
        #print(json.dumps(data, indent=4))  # Imprime en formato bonito (pretty)
        return pdf_base_64
    else:
        print(f"Error en solicitud protegida: {response.status_code}")
        return None
