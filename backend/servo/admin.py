from django.contrib import admin
from .models import Servo

@admin.register(Servo)
class ServoAdmin(admin.ModelAdmin):
    # Campos a mostrar en la lista de registros
    list_display = ('id', 'angle', 'created_at')
    
    # Filtros laterales
    list_filter = ('created_at',)
    
    # Campos de búsqueda
    search_fields = ('angle',)
    
    # Orden por defecto (más recientes primero)
    ordering = ('-created_at',)
    
    # Campos editables directamente en la lista
    list_editable = ('angle',)  # Permite editar el ángulo sin entrar al detalle
    
    # Campos protegidos contra edición
    readonly_fields = ('created_at',)
    
    # Personalización del formulario de edición
    fieldsets = (
        ('Configuración del Servo', {
            'fields': ('angle', 'created_at'),
            'description': 'Controla el ángulo del servo (0° a 180°)'
        }),
    )