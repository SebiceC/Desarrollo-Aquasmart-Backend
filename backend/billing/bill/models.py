from django.db import models
from django.utils import timezone
from datetime import timedelta
from billing.company.models import Company
from users.models import CustomUser
from plots_lots.models import Lot
from billing.rates.models import FixedConsumptionRate, VolumetricConsumptionRate

STATUS_CHOICES = [
    ('pendiente', 'Pendiente'), # Indica si la factura NO ha sido validada por la DIAN
    ('validada', 'Validada'), # Indica que la factura ha sido validada por la DIAN
    ('pagada', 'Pagada'), # Indica que la factura ha sido pagada por el usuario correspondiente
    ('vencida', 'Vencida'), # Indica que la factura ha expirado sin haberse cancelado
    ]

class Bill(models.Model):
    """Modelo para almacenar los datos de la factura."""
    id_bill = models.AutoField(primary_key=True, verbose_name="ID de la factura", help_text="ID de la factura")
    code = models.CharField(unique=True, max_length=7, verbose_name="Código de la factura", help_text="Código de la factura")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, verbose_name="Empresa", help_text="Empresa que emite la factura")
    client = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Cliente", help_text="Cliente o usuario al que se emite la factura")
    lot = models.ForeignKey(Lot, on_delete=models.CASCADE, verbose_name="ID lote", help_text="ID del lote al que se aplica la factura")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pendiente', verbose_name="Estado de la factura", help_text="Estado actual de la factura")
    cufe = models.CharField(unique=True, max_length=96, null=True, blank=True, verbose_name="CUFE", help_text="Código único de la factura electrónica")
    step_number = models.CharField(unique=True, max_length=13, null=True, blank=True, verbose_name="Número de paso", help_text="Número de paso en el proceso de facturación")
    fixed_consumption_rate = models.ForeignKey(FixedConsumptionRate, on_delete=models.CASCADE, null=True, blank=True,  verbose_name="Tarifa fija", help_text="Tarifa fija por consumo")
    volumetric_consumption_rate = models.ForeignKey(VolumetricConsumptionRate, on_delete=models.CASCADE, null=True, blank=True, verbose_name="Tarifa volumétrica", help_text="Tarifa volumétrica por consumo")
    fixed_rate_quantity = models.PositiveIntegerField(verbose_name="Cantidad fija", help_text="Cantidad fija de consumo")
    volumetric_rate_quantity = models.PositiveIntegerField(verbose_name="Cantidad volumétrica", help_text="Cantidad volumétrica de consumo")
    total_fixed_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total tarifa fija", help_text="Total de la tarifa fija")
    total_volumetric_rate = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total tarifa volumétrica", help_text="Total de la tarifa volumétrica")
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total a pagar", help_text="Total a pagar por la factura")
    creation_date = models.DateField(auto_now_add=True, verbose_name="Fecha de creación", help_text="Fecha de creación de la factura")
    dian_validation_date = models.DateTimeField(null=True, blank=True, verbose_name="Fecha de validación por la DIAN", help_text="Fecha en cuya factura ha sido validada por la DIAN")
    due_payment_date = models.DateField(null=True, blank=True, verbose_name="Fecha de vencimiento", help_text="Fecha de vencimiento del pago")
    payment_date = models.DateField(null=True, blank=True, verbose_name="Fecha de pago", help_text="Fecha en la que se realizó el pago")    
    pdf_bill_name = models.CharField(max_length=8, blank=True, default="", verbose_name="Nombre del PDF", help_text="Nombre del archivo PDF de la factura")
    pdf_base64 = models.TextField(null=True, blank=True, verbose_name="PDF Base64", help_text="PDF de la factura en formato Base64")
    qr_url = models.CharField(unique=True, max_length=200, null=True, blank=True, verbose_name="URL QR", help_text="URL del código QR asociado a la factura")

    # --- Campos desnormalizados para histórico ---
    # Empresa
    company_name = models.CharField(blank=True, default="", max_length=255, verbose_name="Nombre empresa", help_text="Nombre de la empresa emisora")
    company_nit = models.CharField(blank=True, default="", max_length=50, verbose_name="NIT empresa", help_text="NIT de la empresa emisora")
    company_address = models.CharField(blank=True, default="", max_length=255, verbose_name="Dirección empresa", help_text="Dirección de la empresa emisora")
    company_phone = models.CharField(blank=True, default="", max_length=50, verbose_name="Teléfono empresa", help_text="Teléfono de la empresa emisora")
    company_email = models.EmailField(blank=True, default="", max_length=255, verbose_name="Correo empresa", help_text="Correo electrónico de la empresa emisora")
    # Cliente
    client_name = models.CharField(blank=True, default="", max_length=255, verbose_name="Nombre cliente", help_text="Nombre del cliente")
    client_document = models.CharField(blank=True, default="", max_length=50, verbose_name="Documento cliente", help_text="Documento del cliente")
    client_address = models.CharField(blank=True, default="", max_length=255, verbose_name="Dirección cliente", help_text="Dirección del cliente")
    # Lote y predio
    lot_code = models.CharField(blank=True, default="", max_length=50, verbose_name="ID de lote", help_text="ID de lote asociado")
    plot_name = models.CharField(blank=True, default="", max_length=255, verbose_name="Nombre predio", help_text="Nombre del predio asociado al lote")
    # Tarifa fija
    fixed_rate_code = models.CharField(blank=True, default="", max_length=50, verbose_name="Código tarifa fija", help_text="Código de la tarifa fija")
    fixed_rate_name = models.CharField(blank=True, default="", max_length=255, verbose_name="Nombre tarifa fija", help_text="Nombre descriptivo de la tarifa fija")
    fixed_rate_value = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, verbose_name="Valor tarifa fija", help_text="Valor de la tarifa fija")
    # Tarifa volumétrica
    volumetric_rate_code = models.CharField(blank=True, default="", max_length=50, verbose_name="Código tarifa volumétrica", help_text="Código de la tarifa volumétrica")
    volumetric_rate_name = models.CharField(blank=True, default="", max_length=255, verbose_name="Nombre tarifa volumétrica", help_text="Nombre descriptivo de la tarifa volumétrica")
    volumetric_rate_value = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, verbose_name="Valor tarifa volumétrica", help_text="Valor de la tarifa volumétrica")

    class Meta:
        verbose_name = "Factura"
        verbose_name_plural = "Facturas"

    def __str__(self):
        return f"{self.code} - Sr.(a) {self.client_name}"

    def save(self, *args, **kwargs):
        # Guardar factura con código AQ00001, AQ00002, etc.
        if not self.code:
            prefix = "AQ"
            last_bill = Bill.objects.filter(code__startswith=prefix).order_by('-id_bill').first()
            if last_bill and last_bill.code[2:].isdigit():
                last_number = int(last_bill.code[2:])
            else:
                last_number = 0
            new_number = last_number + 1
            self.code = f"{prefix}{new_number:05d}"

        # Asignar cliente en la factura según dueño de lote
        if self.lot and not self.client:
            self.client = self.lot.plot.owner

        # Asignar tarifas automáticamente según el tipo de cultivo del lote
        if self.lot and (not self.fixed_consumption_rate or not self.volumetric_consumption_rate):
            crop_type = self.lot.crop_type
            # Buscar la tarifa fija correspondiente al tipo de cultivo
            if not self.fixed_consumption_rate:
                self.fixed_consumption_rate = FixedConsumptionRate.objects.filter(crop_type=crop_type).first()
            # Buscar la tarifa volumétrica correspondiente al tipo de cultivo
            if not self.volumetric_consumption_rate:
                self.volumetric_consumption_rate = VolumetricConsumptionRate.objects.filter(crop_type=crop_type).first()

        # Verificar si se está creando una instancia nueva
        if self._state.adding:
        # Poblar campos desnormalizados de empresa
            if self.company:
                self.company_name = self.company.name
                self.company_nit = self.company.nit
                self.company_address = self.company.address
                self.company_phone = self.company.phone
                self.company_email = self.company.email

            # Poblar campos desnormalizados de cliente
            if self.client:
                # Si tienes get_full_name, úsalo; si no, concatena nombres
                if hasattr(self.client, 'get_full_name'):
                    self.client_name = self.client.get_full_name()
                else:
                    self.client_name = f"{self.client.first_name} {self.client.last_name}"
                self.client_document = self.client.document
                self.client_address = self.client.address

            # Poblar campos desnormalizados de lote y predio
            if self.lot:
                self.lot_code = self.lot.id_lot
                self.plot_name = self.lot.plot.plot_name

            # Poblar campos desnormalizados de tarifa fija
            if self.fixed_consumption_rate:
                self.fixed_rate_code = self.fixed_consumption_rate.code
                self.fixed_rate_name = f"{self.fixed_consumption_rate._meta.verbose_name} {self.fixed_consumption_rate.crop_type.name}"
                self.fixed_rate_value = self.fixed_consumption_rate.fixed_rate_cents / 100

            # Poblar campos desnormalizados de tarifa volumétrica
            if self.volumetric_consumption_rate:
                self.volumetric_rate_code = self.volumetric_consumption_rate.code
                self.volumetric_rate_name = f"{self.volumetric_consumption_rate._meta.verbose_name} {self.volumetric_consumption_rate.crop_type.name}"
                self.volumetric_rate_value = self.volumetric_consumption_rate.volumetric_rate_cents / 100

            # Calcular totales automáticamente
            self.total_fixed_rate = (self.fixed_rate_value or 0) * (self.fixed_rate_quantity or 0)
            self.total_volumetric_rate = (self.volumetric_rate_value or 0) * (self.volumetric_rate_quantity or 0)
            self.total_amount = self.total_fixed_rate + self.total_volumetric_rate

        # Asignar fecha de vencimiento 10 días después de la creación
        if not self.due_payment_date:
            creation = self.creation_date or timezone.now().date()
            self.due_payment_date = creation + timedelta(days=15)        

        # Crear el nombre del PDF de la factura
        if self.code and not self.pdf_bill_name:
            self.pdf_bill_name = f"{self.code[:2]}_{self.code[2:]}"

        # Asignar fecha de pago cuando el status cambia a 'pagada'
        if self.pk:
            old = Bill.objects.get(pk=self.pk)
            if old.status != 'pagada' and self.status == 'pagada':
                self.payment_date = timezone.now().date()
        else:
            if self.status == 'pagada':
                self.payment_date = timezone.now().date()

        super().save(*args, **kwargs)