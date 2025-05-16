from django.db import models
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from communication.requests.models import FlowRequest
from communication.reports.models import FailureReport
from communication.utils import generate_unique_id, change_status_request_report
from communication.notifications import (
    send_assignment_notification,
    send_maintenance_report_notification
)

class Assignment(models.Model):
    """Modelo para almacenar asignaciones de solicitudes y reportes de fallos"""
    id = models.IntegerField(primary_key=True, verbose_name="ID", help_text="Identificador único de la asignación")
    flow_request = models.ForeignKey(FlowRequest, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Solicitud de caudal", help_text="Solicitud de caudal asociada a la asignación")
    failure_report = models.ForeignKey(FailureReport, null=True, blank=True, on_delete=models.CASCADE, verbose_name="Reporte de fallo", help_text="Reporte de fallo asociado a la asignación")
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments_made', verbose_name="Usuario que asigna", help_text="Usuario que realiza la asignación")
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='assignments_received', verbose_name="Usuario a asignar", help_text="Usuario al que se le asigna la solicitud/reporte")
    assignment_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de asignación", help_text="Fecha y hora en que se realizó la asignación")
    reassigned = models.BooleanField(default=False, verbose_name="Fue reasignado", help_text="Indica si la solicitud/reporte ha sido reasignada")

    class Meta:
        verbose_name = "Asignación de solicitud/reporte"
        verbose_name_plural = "Asignaciones de solicitudes/reportes"
        permissions = [
            ("can_be_assigned", "Puede puede ser asignado"),
            ("can_assign_user", "Puede asignar un usuario"),
            ('Can_view_assignment', 'Puede ver asignaciones'),
            ('view_all_assignments', 'Puede ver todas las asignaciones'),
            
        ]

    def __str__(self):
        if self.flow_request:
            return f"Asignación de {self.assigned_by} a {self.assigned_to} ({self.assignment_date} - {self.flow_request.status})"
        if self.failure_report:
            return f"Asignación de {self.assigned_by} a {self.assigned_to} ({self.assignment_date} - {self.failure_report.status})"

    def _validate_requires_delegation(self):
        ''' Valida que no se permita crear una asignación de una solicitud que no debe ser delegada '''
        if self.flow_request and self.flow_request.requires_delegation == False:
            raise ValueError({"error": "No se puede crear una asignación de esta solicitud."})

    def save(self, *args, **kwargs):
        is_new = not self.pk  # Verificar si es una nueva asignación
        
        if not self.pk:
            change_status_request_report(self, Assignment)
        
        if not self.id:
            self.id = generate_unique_id(Assignment,"30")

        if self.flow_request:
            self._validate_requires_delegation()

        super().save(*args, **kwargs)
        
        # Enviar notificación después de guardar
        if is_new:
            send_assignment_notification(self)


class MaintenanceReport(models.Model):
    """Modelo para almacenar informes de mantenimiento"""
    id = models.IntegerField(primary_key=True, verbose_name="ID", help_text="Identificador único del informe de mantenimiento")
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, verbose_name="Asignación", help_text="Asignación asociada al informe de mantenimiento")
    intervention_date = models.DateTimeField(verbose_name="Fecha de intervención", help_text="Fecha y hora en que se realizó la intervención")
    images = models.TextField(null=True, blank=True, verbose_name="Imágenes", help_text="Imágenes de la intervención realizada")
    description = models.TextField(null=True, blank=True, verbose_name="Descripción", help_text="Descripción de la intervención realizada")
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

    def _validate_intervention_date(self):
        ''' Valida que la fecha de intervención no sea mayor a la fecha actual '''
        if self.intervention_date > timezone.now():
            raise ValueError("La fecha de intervención no puede ser mayor a la fecha actual.")

    def _finalize_requests_reports(self):
        ''' Finalizar la solicitud o el reporte ligado al informe después de aprobado '''
        with transaction.atomic():
            if self.is_approved == True:
                if self.assignment.flow_request:
                    self.assignment.flow_request.approve_from_maintenance()
                elif self.assignment.failure_report:
                    self.assignment.failure_report.status = 'Finalizado'
                    self.assignment.failure_report.finalized_at = timezone.now()
                    self.assignment.failure_report.save(update_fields=['status', 'finalized_at'])

    def save(self, *args, **kwargs):
        is_new = not self.pk  # Verificar si es un nuevo informe
        
        if not self.pk:
            change_status_request_report(self, MaintenanceReport)
            
        if not self.id:
            self.id = generate_unique_id(MaintenanceReport,"40")

        self._validate_intervention_date()
        super().save(*args, **kwargs)
        
        self._finalize_requests_reports()
        
        # Enviar notificación después de guardar
        if is_new:
            send_maintenance_report_notification(self)