from django.db import models

class Company(models.Model):
    """
    Modelo para almacenar los datos de la empresa.
    """
    id_empresa = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=60)
    nit = models.CharField(max_length=11, unique=True)
    address = models.CharField(max_length=35, null=True, blank=True)
    phone = models.CharField(max_length=10, null=True, blank=True)
    email = models.EmailField(max_length=50, unique=True, null=True, blank=True)

    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Datos de la empresa"