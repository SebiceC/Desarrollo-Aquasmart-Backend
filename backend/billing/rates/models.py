from django.db import models
from plots_lots.models import CropType

class TaxRate(models.Model):
    """
    Modelo para almacenar una tasa impositiva específica (p. ej., IVA, ICA) y su valor.
    Cada tipo de impuesto debe ser único.
    """
    tax_type = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Tarifa de Impuesto",
        help_text="Tipo de la tarifa (e.j., IVA, ICA)"
    )
    tax_value = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        verbose_name="Valor de la tarifa",
        help_text="Valor de la tarifa (e.j., 19.00)"
    )

    def __str__(self):
        return f"{self.tax_type} ({self.tax_value}%)"
    
    class Meta:
        verbose_name = "Tarifa de Impuesto"
        verbose_name_plural = "Tarifas de Impuesto"


class FixedConsumptionRate(models.Model):
    """
    Modelo para almacenar tasas de consumo fijas para diferentes tipos de cultivos.
    Cada tipo de cultivo tendrá una tasa fija única.
    """
    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name="Código de la tarifa fija",
        help_text="Código de la tarifa fija (e.j., TFA, TFP)"
    )
    crop_type = models.OneToOneField(CropType, on_delete=models.CASCADE,
        verbose_name="Tipo de cultivo",
        help_text="Tipo de cultivo (e.j., Agricultura, Psicultura)"
    )
    fixed_rate_cents = models.PositiveIntegerField(
        verbose_name="Tarifa fija",
        help_text="Tarifa fija por consumo en centavos"
    )

    def fixed_rate_pesos(self):
            """Devuelve la tarija fija en pesos."""
            return self.fixed_rate_cents / 100

    def __str__(self):
        return f"{self.crop_type} (Fija: ${self.fixed_rate_pesos():.2f})"
    
    class Meta:
        verbose_name = "Tarifa Fija de Consumo"
        verbose_name_plural = "Tarifas Fijas de Consumo"


class VolumetricConsumptionRate(models.Model):
    """
    Modelo para almacenar tasas de consumo volumétricas para diferentes tipos de cultivos.
    Cada tipo de cultivo tendrá una tasa volumétrica única.
    """
    code = models.CharField(
        max_length=3,
        unique=True,
        verbose_name="Código de la tarifa volumétrica",
        help_text="Código de la tarifa volumétrica (e.j., TVA, TVP)"
    )
    crop_type = models.OneToOneField(CropType, on_delete=models.CASCADE,
        verbose_name="Tipo de cultivo",
        help_text="Tipo de cultivo (e.j., Agricultura, Psicultura)"
    )
    volumetric_rate_cents = models.PositiveIntegerField(
        verbose_name="Tarifa volumétrica",
        help_text="Tarifa por unidad de volumen (m³) en centavos"
    )

    def volumetric_rate_pesos(self):
        """Devuelve la tarifa volumétrica en pesos."""
        return self.volumetric_rate_cents / 100

    def __str__(self):
        return f"{self.crop_type} (Vol: ${self.volumetric_rate_pesos():.2f})"
    
    class Meta:
        verbose_name = "Tarifa Volumétrica de Consumo"
        verbose_name_plural = "Tarifas Volumétricas de Consumo"