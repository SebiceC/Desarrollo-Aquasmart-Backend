from django.db import models

class Device(models.Model):
    name = models.CharField(max_length=30, blank=True, null=True, verbose_name="Nombre")
    characteristics = models.CharField(max_length=300, blank=True, null=True, verbose_name="Características")
    id_predio = models.IntegerField(blank=True, null=True, verbose_name="ID Predio")
    id_lote = models.IntegerField(blank=True, null=True, verbose_name="ID Lote")

    def __str__(self):
        return f"Dispositivo IoT: {self.name} (ID: {self.id})"