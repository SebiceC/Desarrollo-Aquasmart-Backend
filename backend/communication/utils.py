import hashlib
import uuid
from .models import StatusRequestReport

def generate_unique_id(model,prefix):
        """Genera un ID único para el modelo dado, asegurando que no exista en la base de datos"""
        while True:
            unique_value = str(uuid.uuid4())
            hash_obj = hashlib.md5(unique_value.encode())
            hash_int = int(hash_obj.hexdigest(), 16)
            numeric_part = str(hash_int)[:6] # toma los primeros 6 digitos del hash
            generated_id = prefix + numeric_part# Genera el ID único con el prefijo
            #Verifica si el ID Ya existe en la base de datos            
            if not model.objects.filter(id=generated_id).exists():
                # Si no existe, devuelve el ID generado
                return int(generated_id)

def change_status_request_report(self, model):
    ''' Cambia el estado de la solicitud o reporte '''

    if model.__name__ == "Assignment":
        flow_request = self.flow_request
        failure_report = self.failure_report
        if flow_request:
            model_flow_request = type(flow_request).objects.filter(pk=flow_request.pk)
            model_flow_request.update(status=StatusRequestReport.IN_PROGRESS)
        elif failure_report:
            model_failure_report = type(failure_report).objects.filter(pk=failure_report.pk)
            model_failure_report.update(status=StatusRequestReport.IN_PROGRESS)

    if model.__name__ == "MaintenanceReport":
        flow_request = self.assignment.flow_request
        failure_report = self.assignment.failure_report

        if flow_request:
            model_flow_request = type(flow_request).objects.filter(pk=flow_request.pk)
            model_flow_request.update(status=StatusRequestReport.REJECTED)
        elif failure_report:
            model_failure_report = type(failure_report).objects.filter(pk=failure_report.pk)
            model_failure_report.update(status=StatusRequestReport.REJECTED)