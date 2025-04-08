from django.db import models

class Company(models.Model):
    """
    Modelo para almacenar los datos de la empresa.
    """
    id_empresa = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60)
    nit = models.CharField(max_length=11, unique=True)
    ciudad = models.CharField(max_length=15)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Datos de la empresa"