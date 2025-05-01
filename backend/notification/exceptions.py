from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)
    
    if response is not None:
        error_data = {
            'error': {
                'code': response.status_code,
                'message': response.data.get('detail', str(response.data)),
                'type': exc.__class__.__name__
            }
        }
        response.data = error_data
    
    return response