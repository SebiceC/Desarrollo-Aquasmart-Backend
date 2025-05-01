from django.db.models.signals import post_save
from django.dispatch import receiver
from reportes.models import Reporte
from django.contrib.auth.models import Group
from reportes.models import InformeMantenimiento
from notification.utils.notifiers import NotificationHandler

@receiver(post_save, sender=Reporte)
def notificar_creacion_reporte(sender, instance, created, **kwargs):
    if created:
        try:
            grupo_admin = Group.objects.get(name='Administradores')
            administradores = grupo_admin.user_set.all()
            
            for admin in administradores:
                NotificationHandler.create_notification(
                    instance,
                    'REPORT_CREATED',
                    admin,
                    metadata={
                        'report_id': instance.id,
                        'titulo': instance.titulo,
                        'tipo': instance.get_tipo_display()
                    }
                )
        except Group.DoesNotExist:
            pass  # O maneja el error según necesites

@receiver(post_save, sender=InformeMantenimiento)
def notificar_informe_completado(sender, instance, **kwargs):
    if instance.estado == 'COMPLETADO' and instance.aprobado:
        # Obtener todos los administradores
        grupo_admin = Group.objects.get(name='Administradores')
        administradores = grupo_admin.user_set.all()
        
        for admin in administradores:
            NotificationHandler.create_notification(
                instance,
                'REPORT_COMPLETED',
                admin,
                metadata={
                    'report_id': instance.reporte.id,
                    'tecnico': instance.tecnico.get_full_name(),
                    'solucion': instance.descripcion_solucion[:100] + '...',
                    'fecha_completado': instance.fecha_fin.strftime("%d/%m/%Y %H:%M")
                }
            )        