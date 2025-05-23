from django.db import models
from users.models import CustomUser
import hashlib
import uuid
class Plot(models.Model):
    id_plot = models.CharField(primary_key=True,max_length=10, verbose_name="ID de predio")
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="dueño_de_predio")
    plot_name = models.CharField(max_length= 20, db_index=True, null=False, blank=False, verbose_name="Nombre de predio")
    latitud =  models.DecimalField(max_digits=9, decimal_places=6, null=False, blank=False, verbose_name="Longitud de predio")
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=False, blank=False, verbose_name="Latitud de predio")
    plot_extension =models.DecimalField(max_digits=8, decimal_places=2, null=False, blank=False, verbose_name="Extensión de tierra")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    is_activate = models.BooleanField(default=True, help_text="Indica si el predio esta habilitado", db_index=True, verbose_name="estado predio")
    
    REQUIRED_FIELDS = ['owner','plot_name','latitud','longitud','plot_extension']
    
    class Meta:
        verbose_name = "Predio"
        verbose_name_plural = "Predios"
    
    def save(self, *args, **kwargs):
        # Generar el código solo si no existe aún
        if not self.id_plot:           
                        
            unique_value = str(uuid.uuid4())
    
    
            # Crear el hash MD5 del valor
            hash_obj = hashlib.md5(unique_value.encode())
            
            # Convertir el hash hexadecimal a un entero
            hash_int = int(hash_obj.hexdigest(), 16)
            
            # Convertir el entero en una cadena numérica y truncar a la longitud deseada
            hash_str = str(hash_int)[:7]           
            
            # Generar el código
            self.id_plot = f"PR-{hash_str}"
            print (self.id_plot)
        # Generar el código de la receta
        super().save(*args, **kwargs)    
    def __str__(self):
        return f"{self.plot_name} (ID: {self.id_plot})"
    
class SoilType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Tipo de suelo")
    
    class Meta:
        verbose_name = "Tipo de suelo"
        verbose_name_plural = "Tipos de suelo"
    
    def __str__(self):
        return self.name
    
class CropType(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Tipo de cultivo")
    
    class Meta:
        verbose_name = "Tipo de cultivo"
        verbose_name_plural = "Tipos de cultivo"
    
    def __str__(self):
        return self.name
    
class Lot(models.Model):
    plot = models.ForeignKey(Plot, on_delete=models.CASCADE, related_name="lotes", verbose_name="Predio")
    id_lot = models.CharField(primary_key=True, max_length=15, unique=True, editable=False, verbose_name="ID de lote")  # Campo para almacenar el ID único
    crop_name = models.CharField(max_length=20, default="Sin nombre", null=False, blank=False, verbose_name="Nombre del cultivo")
    crop_type = models.ForeignKey(CropType, on_delete=models.CASCADE, verbose_name="Tipo de cultivo")
    crop_variety = models.CharField(max_length=20, null=True, blank=True, verbose_name="Variedad del cultivo")
    soil_type = models.ForeignKey(SoilType, on_delete=models.CASCADE, verbose_name="Tipo de suelo")
    is_activate = models.BooleanField(default=True, help_text="Indica si el lote esta habilitado", db_index=True, verbose_name="estado lote")
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de registro")
    
    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
    
    def __str__(self):
        return f"Lote {self.id_lot} en {self.plot.plot_name} - {self.crop_type}"
    
    def save(self, *args, **kwargs):
        # Generar el id_lot solo si no existe aún
        if not self.id_lot:
            # Obtener el id_plot del predio asociado
            id_plot = self.plot.id_plot  # Ejemplo: "PR-1234567"
            
            # Eliminar el prefijo "PR-" del id_plot
            id_plot_sin_prefijo = id_plot.replace("PR-", "")  # Resultado: "1234567"
            
            # Obtener el número de lotes ya existentes para este predio
            lotes_del_predio = Lot.objects.filter(plot=self.plot).count()
            
            # Generar el número secuencial (inicia en 1)
            numero_secuencial = lotes_del_predio + 1
            
            # Formatear el número secuencial con 3 dígitos (001, 002, etc.)
            numero_formateado = f"{numero_secuencial:03}"
            
            # Crear el id_lot combinando id_plot sin prefijo y el número secuencial
            self.id_lot = f"{id_plot_sin_prefijo}-{numero_formateado}"  # Resultado: "1234567-001"
        
        # Guardar el objeto
        super().save(*args, **kwargs)     
    
    