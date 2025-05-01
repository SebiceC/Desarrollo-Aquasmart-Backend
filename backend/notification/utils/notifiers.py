from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils import timezone
from notification.models import EmailNotification, Notification
import logging

logger = logging.getLogger(__name__)

class NotificationHandler:
    
    @staticmethod
    def create_notification(content_object, notification_type, recipient, metadata=None):
        try:
            # Validación de email
            if not recipient.email:
                raise ValueError(f"Usuario {recipient.username} no tiene email registrado")
            
            notification = Notification.objects.create(
                content_object=content_object,
                notification_type=notification_type,
                recipient=recipient,
                metadata=metadata or {}
            )
            
            if settings.NOTIFICATION_CONFIG['ENABLED_CHANNELS']['EMAIL']:
                return NotificationHandler._send_email_sync(notification)
            
            return notification
        except Exception as e:
            logger.error(f"Error creando notificación: {str(e)}")
            return None

    @staticmethod
    def _send_email_sync(notification):
        try:
            # Configuración del email
            template_config = settings.NOTIFICATION_CONFIG['TEMPLATES']['EMAIL'].get(
                notification.notification_type, {}
            )
            
            context = {
                'notification': notification,
                'object': notification.content_object,
                'metadata': notification.metadata,
                'app_name': settings.NOTIFICATION_CONFIG.get('APP_NAME', 'AquaSmart')
            }

            # Crear registro en BD antes de enviar
            email_notification = EmailNotification.objects.create(
                notification=notification,
                subject=template_config['subject'].format(**notification.metadata),
                status='PENDING'
            )

            # Envío real
            email = EmailMultiAlternatives(
                subject=email_notification.subject,
                body=render_to_string('emails/base.txt', context),
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[notification.recipient.email],
            )
            email.attach_alternative(
                render_to_string(template_config['path'], context), 
                "text/html"
            )
            email.send()

            # Actualizar estado
            email_notification.status = 'SENT'
            email_notification.sent_at = timezone.now()
            email_notification.save()
            
            return notification
        except Exception as e:
            logger.error(f"Error enviando email: {str(e)}")
            if 'email_notification' in locals():
                email_notification.status = 'FAILED'
                email_notification.error_message = str(e)
                email_notification.save()
            return None
        
        