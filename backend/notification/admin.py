from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Notification, EmailNotification

class EmailNotificationInline(admin.StackedInline):
    model = EmailNotification
    extra = 0
    readonly_fields = ('status', 'sent_at')
    can_delete = False

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('id', 'tipo_notificacion', 'destinatario', 'objeto_relacionado', 'leida')
    list_filter = ('notification_type', 'is_read')
    inlines = [EmailNotificationInline]
    readonly_fields = ('ver_objeto',)
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('notification_type', 'recipient', 'is_read')
        }),
        ('Contenido', {
            'fields': ('metadata', 'ver_objeto')
        }),
    )
    
    def tipo_notificacion(self, obj):
        return obj.get_notification_type_display()
    tipo_notificacion.short_description = 'Tipo'
    
    def destinatario(self, obj):
        return obj.recipient.email
    destinatario.short_description = 'Email Destinatario'
    
    def objeto_relacionado(self, obj):
        if obj.content_object:
            return str(obj.content_object)
        return "-"
    objeto_relacionado.short_description = "Objeto"
    
    def leida(self, obj):
        return "✅ Sí" if obj.is_read else "❌ No"
    leida.short_description = 'Leída'
    leida.admin_order_field = 'is_read'
    
    def ver_objeto(self, obj):
        if obj.content_object:
            url = reverse(
                f'admin:{obj.content_object._meta.app_label}_{obj.content_object._meta.model_name}_change',
                args=[obj.content_object.id]
            )
            return format_html('<a href="{}">Ver {} #{}</a>', 
                            url, 
                            obj.content_type.model, 
                            obj.content_object.id)
        return "-"
    ver_objeto.short_description = "Enlace al Objeto"