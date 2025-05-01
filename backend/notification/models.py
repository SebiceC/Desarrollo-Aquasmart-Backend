from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from users.models import CustomUser

class Notification(models.Model):
    class NotificationType(models.TextChoices):
        REPORT_CREATED = 'REPORT_CREATED', 'Nuevo Reporte Creado'
        REPORT_ASSIGNED = 'REPORT_ASSIGNED', 'Reporte Asignado'
        REPORT_COMPLETED = 'REPORT_COMPLETED', 'Reporte Completado'
        MAINTENANCE_ASSIGNED = 'MAINTENANCE_ASSIGNED', 'Mantenimiento Asignado'

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    notification_type = models.CharField(max_length=50, choices=NotificationType.choices)
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)

    class Meta:
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['recipient', 'is_read']),
        ]
        ordering = ['-created_at']

class EmailNotification(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        SENT = 'SENT', 'Enviado'
        FAILED = 'FAILED', 'Fallido'

    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, related_name='email_notification')
    subject = models.CharField(max_length=255)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    metadata = models.JSONField(default=dict)  # Añade este campo nuevo

    def __str__(self):
        return f"EmailNotification for {self.notification.id}"