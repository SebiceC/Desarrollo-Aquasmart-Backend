from django.db import models
from django.conf import settings
from communication.requests.models import FlowRequest
from communication.reports.models import FailureReport
from communication.utils import generate_unique_id
from communication.notifications import send_maintenance_report_notification

class Assignment(models.Model):
    """Modelo para almacenar asignaciones de solicitudes y reportes de fallos"""
    id = models.IntegerField(primary_key=True, verbose_name="ID", help_text="Identificador único de la asignación")
    flow_request = models.ForeignKey(FlowRequest, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Solicitud de caudal", help_text="Solicitud de caudal asociada a la asignación")
    failure_report = models.ForeignKey(FailureReport, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Reporte de fallo", help_text="Reporte de fallo asociado a la asignación")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments_made', verbose_name="Usuario que asigna", help_text="Usuario que realiza la asignación")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments_received', verbose_name="Usuario a asignar", help_text="Usuario al que se le asigna la solicitud/reporte")
    assignment_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de asignación", help_text="Fecha y hora en que se realizó la asignación")
    reassigned = models.BooleanField(default=False, verbose_name="Fue reasignado", help_text="Indica si la solicitud/reporte ha sido reasignada")
    observations = models.TextField(null=True, blank=True, verbose_name="Observaciones", help_text="Observaciones adicionales sobre la asignación")

    class Meta:
        verbose_name = "Asignación de solicitud/reporte"
        verbose_name_plural = "Asignaciones de solicitudes/reportes"         
     
    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if not self.id:
            self.id = generate_unique_id(Assignment, "30")
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Asignación #{self.id} de {self.assigned_by} a {self.assigned_to}"

class MaintenanceReport(models.Model):
    """Modelo para almacenar informes de mantenimiento"""
    id = models.IntegerField(primary_key=True, verbose_name="ID", help_text="Identificador único del informe de mantenimiento")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="Asignación", help_text="Asignación asociada al informe de mantenimiento")
    intervention_date = models.DateTimeField(verbose_name="Fecha de intervención", help_text="Fecha y hora en que se realizó la intervención")
    images = models.TextField(null=True, blank=True, verbose_name="Imágenes", help_text="Imágenes de la intervención realizada (en base64 o URLs)")
    description = models.TextField(null=True, blank=True, verbose_name="Descripción", help_text="Descripción detallada de la intervención realizada")
    findings = models.TextField(null=True, blank=True, verbose_name="Hallazgos", help_text="Problemas encontrados durante la intervención")
    actions_taken = models.TextField(null=True, blank=True, verbose_name="Acciones realizadas", help_text="Acciones tomadas para resolver los problemas")
    recommendations = models.TextField(null=True, blank=True, verbose_name="Recomendaciones", help_text="Recomendaciones para futuras intervenciones")
    status = models.CharField(max_length=50, choices=[
        ('Finalizado', 'Finalizado'), 
        ('Requiere nueva intervención', 'Requiere nueva intervención')
    ], verbose_name="Estado", help_text="Estado final del informe de mantenimiento")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación", help_text="Fecha y hora en que se creó el informe de mantenimiento")
    is_approved = models.BooleanField(default=False, verbose_name="Fue aprobado", help_text="Indica si el informe de mantenimiento fue aprobado o no")

    class Meta:
        verbose_name = "Informe de mantenimiento"
        verbose_name_plural = "Informes de mantenimiento"

    def __str__(self):
        return f"Informe #{self.id} por {self.assignment.assigned_to} ({self.status})"

    def _finalize_requests_reports(self):
        ''' Finalizar la solicitud o el reporte ligado al informe después de aprobado '''
        if self.is_approved:
            if self.assignment.flow_request:
                self.assignment.flow_request.is_approved = True
                self.assignment.flow_request.save()
            elif self.assignment.failure_report:
                self.assignment.failure_report.status = 'Finalizado'
                self.assignment.failure_report.save()

    def save(self, *args, **kwargs):
        is_new = not self.pk
        
        if not self.id:
            self.id = generate_unique_id(MaintenanceReport, "40")

        super().save(*args, **kwargs)
        
        self._finalize_requests_reports()
        
        if is_new:
            send_maintenance_report_notification(self)