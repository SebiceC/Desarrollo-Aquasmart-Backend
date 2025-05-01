from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django.contrib import messages
from django.contrib.auth import get_user_model 
from django.core.exceptions import ValidationError
from django.contrib.auth.models import Group
from .models import Reporte, Asignacion, InformeMantenimiento
from notification.utils.notifiers import NotificationHandler

User = get_user_model()

class InformeMantenimientoInline(admin.StackedInline):
    model = InformeMantenimiento
    extra = 0
    fields = ('tecnico', 'descripcion_solucion', 'estado', 'fecha_fin')
    readonly_fields = ('fecha_inicio',)
    fk_name = 'reporte'

class AsignacionInline(admin.StackedInline):
    model = Asignacion
    extra = 0
    fields = ('tecnico', 'fecha_limite', 'instrucciones', 'estado')
    readonly_fields = ('fecha_asignacion',)
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tecnico":
            kwargs["queryset"] = User.objects.filter(groups__name='Tecnicos')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    list_display = ('id', 'titulo', 'tipo', 'estado', 'creado_por', 'fecha_creacion', 'acciones')
    list_filter = (
        'tipo',
        ('creado_por', admin.RelatedOnlyFieldListFilter),
        ('fecha_creacion', admin.DateFieldListFilter),
    )
    search_fields = ('id', 'titulo', 'creado_por__username', 'descripcion')
    date_hierarchy = 'fecha_creacion'
    inlines = [AsignacionInline, InformeMantenimientoInline]
    actions = ['marcar_como_aceptado', 'marcar_como_rechazado']
    
    fieldsets = (
        (None, {
            'fields': ('titulo', 'descripcion', 'tipo')
        }),
        ('Responsables', {
            'fields': ('creado_por',)
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('estado',) + super().get_readonly_fields(request, obj)
        return super().get_readonly_fields(request, obj)

    def acciones(self, obj):
        return format_html(
            '<a class="button" href="{}">Gestionar</a>',
            f'/admin/reportes/reporte/{obj.id}/change/'
        )

    def marcar_como_aceptado(self, request, queryset):
        for reporte in queryset:
            if reporte.tipo in ['CAUDAL', 'APLICATIO']:
                reporte.estado = 'ACEPTADO'
                reporte.save()
                self.message_user(request, f"Reporte {reporte.id} aceptado")
    marcar_como_aceptado.short_description = "Aceptar reportes seleccionados"

    def marcar_como_rechazado(self, request, queryset):
        for reporte in queryset:
            if reporte.tipo in ['CAUDAL', 'APLICATIO']:
                reporte.estado = 'RECHAZADO'
                reporte.save()
                self.message_user(request, f"Reporte {reporte.id} rechazado")
    marcar_como_rechazado.short_description = "Rechazar reportes seleccionados"

    def save_model(self, request, obj, form, change):
        try:
            if not change:
                obj.creado_por = request.user
                obj.estado = 'PENDIENTE'
            
            super().save_model(request, obj, form, change)
            
            if not change:
                NotificationHandler.create_notification(
                    obj,
                    'REPORT_CREATED',
                    request.user,
                    metadata={
                        'report_id': obj.id,
                        'titulo': obj.titulo,
                        'prioridad': 'alta'
                    }
                )
                messages.success(request, "Reporte creado y notificación enviada")
        except Exception as e:
            messages.error(request, f"Error al crear reporte: {str(e)}")

@admin.register(Asignacion)
class AsignacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporte', 'tecnico', 'estado', 'fecha_asignacion', 'estado_asignacion')
    list_filter = ('estado', 'tecnico', 'fecha_asignacion')
    search_fields = ('reporte__id', 'reporte__titulo', 'tecnico__username', 'instrucciones')
    date_hierarchy = 'fecha_asignacion'
    readonly_fields = ('fecha_asignacion',)
    
    fieldsets = (
        (None, {
            'fields': ('reporte', 'tecnico', 'estado')
        }),
        ('Detalles', {
            'fields': ('fecha_limite', 'instrucciones')
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tecnico":
            kwargs["queryset"] = User.objects.filter(groups__name='Tecnicos')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def estado_asignacion(self, obj):
        return "✅ Activa" if obj.fecha_limite > timezone.now() else "⏰ Expirada"
    estado_asignacion.short_description = 'Estado'

    def save_model(self, request, obj, form, change):
        try:
            # Validación adicional
            if not obj.tecnico.email:
                raise ValidationError("El técnico asignado no tiene email registrado")
            
            obj.full_clean()
            super().save_model(request, obj, form, change)
            
            # Notificación
            NotificationHandler.create_notification(
                obj,
                'REPORT_ASSIGNED',
                obj.tecnico,
                metadata={
                    'report_id': obj.reporte.id,
                    'titulo': obj.reporte.titulo,
                    'fecha_limite': obj.fecha_limite.strftime("%d/%m/%Y"),
                    'instrucciones': obj.instrucciones,
                    'prioridad': 'alta' if obj.reporte.tipo == 'INCIDENTE' else 'media'
                }
            )
            messages.success(request, "Asignación registrada y notificación enviada")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

@admin.register(InformeMantenimiento)
class InformeMantenimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'reporte', 'tecnico', 'estado', 'aprobado', 'fecha_fin')
    list_filter = ('estado', 'aprobado', 'tecnico')
    readonly_fields = ('fecha_inicio',)
    
    fieldsets = (
        (None, {
            'fields': ('reporte', 'asignacion', 'tecnico', 'estado', 'aprobado')
        }),
        ('Solución', {
            'fields': ('descripcion_solucion', 'fecha_fin')
        }),
    )

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "tecnico":
            kwargs["queryset"] = User.objects.filter(groups__name='Tecnicos')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)