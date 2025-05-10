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
            flow_request.status = StatusRequestReport.IN_PROGRESS
            flow_request.save(update_fields=['status'])
        elif failure_report:
            failure_report.status = StatusRequestReport.IN_PROGRESS
            failure_report.save(update_fields=['status'])

    if model.__name__ == "MaintenanceReport":
        flow_request = self.assignment.flow_request
        failure_report = self.assignment.failure_report

        if flow_request:
            flow_request.status = StatusRequestReport.REJECTED
            flow_request.save(update_fields=['status'])
        elif failure_report:
            failure_report.status = StatusRequestReport.REJECTED
            failure_report.save(update_fields=['status'])