# Generated by Django 5.1.6 on 2025-04-18 01:25

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0006_fixedconsumptionrate_volumetricconsumptionrate_and_more'),
        ('plots_lots', '0008_croptype_lot_crop_name_alter_lot_crop_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bill',
            fields=[
                ('id_bill', models.AutoField(help_text='ID de la factura', primary_key=True, serialize=False, verbose_name='ID de la factura')),
                ('code', models.CharField(help_text='Código de la factura', max_length=7, unique=True, verbose_name='Código de la factura')),
                ('status', models.CharField(choices=[('pendiente', 'Pendiente'), ('validada', 'Validada'), ('pagada', 'Pagada'), ('vencida', 'Vencida')], default='pendiente', help_text='Estado actual de la factura', max_length=10, verbose_name='Estado de la factura')),
                ('cufe', models.CharField(blank=True, help_text='Código único de la factura electrónica', max_length=96, null=True, unique=True, verbose_name='CUFE')),
                ('step_number', models.CharField(blank=True, help_text='Número de paso en el proceso de facturación', max_length=13, null=True, unique=True, verbose_name='Número de paso')),
                ('fixed_rate_quantity', models.PositiveIntegerField(help_text='Cantidad fija de consumo', verbose_name='Cantidad fija')),
                ('volumetric_rate_quantity', models.PositiveIntegerField(help_text='Cantidad volumétrica de consumo', verbose_name='Cantidad volumétrica')),
                ('total_fixed_rate', models.DecimalField(decimal_places=2, help_text='Total de la tarifa fija', max_digits=10, verbose_name='Total tarifa fija')),
                ('total_volumetric_rate', models.DecimalField(decimal_places=2, help_text='Total de la tarifa volumétrica', max_digits=10, verbose_name='Total tarifa volumétrica')),
                ('total_amount', models.DecimalField(decimal_places=2, help_text='Total a pagar por la factura', max_digits=10, verbose_name='Total a pagar')),
                ('creation_date', models.DateField(auto_now_add=True, help_text='Fecha de creación de la factura', verbose_name='Fecha de creación')),
                ('dian_validation_date', models.DateTimeField(blank=True, help_text='Fecha en cuya factura ha sido validada por la DIAN', null=True, verbose_name='Fecha de validación por la DIAN')),
                ('due_payment_date', models.DateField(blank=True, help_text='Fecha de vencimiento del pago', null=True, verbose_name='Fecha de vencimiento')),
                ('payment_date', models.DateField(blank=True, help_text='Fecha en la que se realizó el pago', null=True, verbose_name='Fecha de pago')),
                ('pdf_bill_name', models.CharField(blank=True, default='', help_text='Nombre del archivo PDF de la factura', max_length=8, verbose_name='Nombre del PDF')),
                ('pdf_base64', models.TextField(blank=True, help_text='PDF de la factura en formato Base64', null=True, verbose_name='PDF Base64')),
                ('qr_url', models.CharField(blank=True, help_text='URL del código QR asociado a la factura', max_length=200, null=True, unique=True, verbose_name='URL QR')),
                ('company_name', models.CharField(blank=True, default='', help_text='Nombre de la empresa emisora', max_length=255, verbose_name='Nombre empresa')),
                ('company_nit', models.CharField(blank=True, default='', help_text='NIT de la empresa emisora', max_length=50, verbose_name='NIT empresa')),
                ('company_address', models.CharField(blank=True, default='', help_text='Dirección de la empresa emisora', max_length=255, verbose_name='Dirección empresa')),
                ('company_phone', models.CharField(blank=True, default='', help_text='Teléfono de la empresa emisora', max_length=50, verbose_name='Teléfono empresa')),
                ('company_email', models.EmailField(blank=True, default='', help_text='Correo electrónico de la empresa emisora', max_length=255, verbose_name='Correo empresa')),
                ('client_name', models.CharField(blank=True, default='', help_text='Nombre del cliente', max_length=255, verbose_name='Nombre cliente')),
                ('client_document', models.CharField(blank=True, default='', help_text='Documento del cliente', max_length=50, verbose_name='Documento cliente')),
                ('client_address', models.CharField(blank=True, default='', help_text='Dirección del cliente', max_length=255, verbose_name='Dirección cliente')),
                ('lot_code', models.CharField(blank=True, default='', help_text='ID de lote asociado', max_length=50, verbose_name='ID de lote')),
                ('plot_name', models.CharField(blank=True, default='', help_text='Nombre del predio asociado al lote', max_length=255, verbose_name='Nombre predio')),
                ('fixed_rate_code', models.CharField(blank=True, default='', help_text='Código de la tarifa fija', max_length=50, verbose_name='Código tarifa fija')),
                ('fixed_rate_name', models.CharField(blank=True, default='', help_text='Nombre descriptivo de la tarifa fija', max_length=255, verbose_name='Nombre tarifa fija')),
                ('fixed_rate_value', models.DecimalField(blank=True, decimal_places=2, help_text='Valor de la tarifa fija', max_digits=10, null=True, verbose_name='Valor tarifa fija')),
                ('volumetric_rate_code', models.CharField(blank=True, default='', help_text='Código de la tarifa volumétrica', max_length=50, verbose_name='Código tarifa volumétrica')),
                ('volumetric_rate_name', models.CharField(blank=True, default='', help_text='Nombre descriptivo de la tarifa volumétrica', max_length=255, verbose_name='Nombre tarifa volumétrica')),
                ('volumetric_rate_value', models.DecimalField(blank=True, decimal_places=2, help_text='Valor de la tarifa volumétrica', max_digits=10, null=True, verbose_name='Valor tarifa volumétrica')),
                ('client', models.ForeignKey(blank=True, help_text='Cliente o usuario al que se emite la factura', null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Cliente')),
                ('company', models.ForeignKey(help_text='Empresa que emite la factura', on_delete=django.db.models.deletion.CASCADE, to='billing.company', verbose_name='Empresa')),
                ('fixed_consumption_rate', models.ForeignKey(blank=True, help_text='Tarifa fija por consumo', null=True, on_delete=django.db.models.deletion.CASCADE, to='billing.fixedconsumptionrate', verbose_name='Tarifa fija')),
                ('lot', models.ForeignKey(help_text='ID del lote al que se aplica la factura', on_delete=django.db.models.deletion.CASCADE, to='plots_lots.lot', verbose_name='ID lote')),
                ('volumetric_consumption_rate', models.ForeignKey(blank=True, help_text='Tarifa volumétrica por consumo', null=True, on_delete=django.db.models.deletion.CASCADE, to='billing.volumetricconsumptionrate', verbose_name='Tarifa volumétrica')),
            ],
            options={
                'verbose_name': 'Factura',
                'verbose_name_plural': 'Facturas',
            },
        ),
    ]
