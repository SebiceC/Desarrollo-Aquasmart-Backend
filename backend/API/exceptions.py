from rest_framework.views import exception_handler
from rest_framework.exceptions import ValidationError
from django.http import JsonResponse

def custom_exception_handler(exc, context):
    # Primero, obtén la respuesta estándar de DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Simplifica los errores de validación
        if isinstance(exc, ValidationError):
            errors = {}
            for field, messages in response.data.items():
                if isinstance(messages, list):
                    errors[field] = messages[0] if messages else "Error desconocido"
                else:
                    errors[field] = str(messages)
            
            response.data = {
                "status": "error",
                "code": response.status_code,
                "errors": errors,
            }
        else:
            # Para otros tipos de errores (ej: PermissionDenied)
            response.data = {
                "status": "error",
                "code": response.status_code,
                "message": str(exc),
            }

    return response