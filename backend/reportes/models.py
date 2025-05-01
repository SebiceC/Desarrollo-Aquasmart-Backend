from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.exceptions import ValidationError
User = get_user_model()

class Reporte(models.Model):
    TIPO_CHOICES = (
        ('MANTENIMIENTO', 'Mantenimiento'),
        ('REPARACION', 'Reparación'),
        ('INCIDENTE', 'Incidente'),
        ('CAUDAL', 'Solicitud de caudal'),
        ('APLICATIO', 'Fallo en aplicativo'),
    )
    
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('ASIGNADO', 'Asignado'),
        ('EN_PROCESO', 'En proceso'),
        ('COMPLETADO', 'Completado'),
    )
    
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tipo = models.CharField(max_length=50, choices=TIPO_CHOICES, default='MANTENIMIENTO')
    estado = models.CharField(
        max_length=50,
        choices=ESTADO_CHOICES,
        default='PENDIENTE',
        editable=False  # Campo no editable en formularios
    )
    creado_por = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='reportes_creados'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.titulo} ({self.get_estado_display()})"

    def save(self, *args, **kwargs):
        if not self.pk:  # Solo para nuevos reportes
            self.estado = 'PENDIENTE'
        super().save(*args, **kwargs)

class Asignacion(models.Model):
    ESTADO_CHOICES = (
        ('PENDIENTE', 'Pendiente'),
        ('ACEPTADA', 'Aceptada'),
        ('RECHAZADA', 'Rechazada'),
        ('COMPLETADA', 'Completada'),
    )
    
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE, related_name='asignaciones')
    tecnico = models.ForeignKey(User, on_delete=models.CASCADE, related_name='asignaciones')
    estado = models.CharField(max_length=50, choices=ESTADO_CHOICES, default='PENDIENTE')
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    fecha_limite = models.DateTimeField()
    instrucciones = models.TextField(blank=True)

    def __str__(self):
        return f"Asignación #{self.id} - {self.reporte.titulo}"

class InformeMantenimiento(models.Model):
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE, related_name='informes')
    asignacion = models.OneToOneField(Asignacion, on_delete=models.CASCADE, related_name='informe')
    tecnico = models.ForeignKey(User, on_delete=models.CASCADE)
    descripcion_solucion = models.TextField()
    image_base64 = models.TextField(blank=True, null=True, verbose_name="Imagen del informe")
    fecha_inicio = models.DateTimeField(auto_now_add=True)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=20,
        choices=(('PENDIENTE', 'Pendiente'), ('COMPLETADO', 'Completado')),
        default='PENDIENTE'
    )

    aprobado = models.BooleanField(default=False, verbose_name="Aprobado por administrador")
    def __str__(self):
        return f"#{self.id} - {self.reporte.titulo}"
    
    def clean(self):
        # Validar que el técnico pertenezca al grupo correcto
        if not self.tecnico.groups.filter(name='Tecnicos').exists():
            raise ValidationError({'tecnico': "El usuario asignado no es un técnico autorizado"})
        # Validar que el técnico sea el mismo que está en la asignación
        if self.tecnico != self.asignacion.tecnico:
            raise ValidationError({'tecnico': "Solo el técnico asignado puede registrar el informe"})
        
        # Validar que el informe completado tenga descripción
        if self.estado == 'COMPLETADO' and not self.descripcion_solucion:
            raise ValidationError({'descripcion_solucion': "Debe registrar la solución para completar el informe"})
        

    def save(self, *args, **kwargs):
        if self.estado == 'COMPLETADO':
            if not self.fecha_fin:
                self.fecha_fin = timezone.now()
            # Validación adicional para aprobación
            if self.aprobado and not self.reporte.estado == 'COMPLETADO':
                self.reporte.estado = 'COMPLETADO'
                self.reporte.save()
        super().save(*args, **kwargs)