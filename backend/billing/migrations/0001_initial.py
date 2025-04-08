# Generated by Django 5.1.6 on 2025-04-07 16:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('plots_lots', '0008_croptype_lot_crop_name_alter_lot_crop_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Company',
            fields=[
                ('id_empresa', models.AutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=60)),
                ('nit', models.CharField(max_length=11)),
                ('ciudad', models.CharField(max_length=15)),
            ],
            options={
                'verbose_name': 'Datos de la empresa',
            },
        ),
        migrations.CreateModel(
            name='TaxRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tax_type', models.CharField(help_text='Tipo de la tarifa (e.j., IVA, ICA)', max_length=20, unique=True, verbose_name='Tarifa de Impuesto')),
                ('tax_value', models.DecimalField(decimal_places=2, help_text='Valor de la tarifa (e.j., 19.00)', max_digits=5, verbose_name='Valor de la tarifa')),
            ],
            options={
                'verbose_name': 'Tarifa de Impuesto',
                'verbose_name_plural': 'Tarifas de Impuestos',
            },
        ),
        migrations.CreateModel(
            name='ConsumptionRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fixed_rate_cents', models.PositiveIntegerField(help_text='Tarifa fija por consumo en centavos (e.j., 100.00 => 10000)', verbose_name='Tarifa fija (centavos)')),
                ('volumetric_rate_cents', models.PositiveIntegerField(help_text='Tarifa por unidad de volumen (m³) en centavos (e.j., 10000)', verbose_name='Tarifa volumétrica (centavos)')),
                ('crop_type', models.ForeignKey(help_text='Tipo de cultivo (e.j., Agricultura, Psicultura)', max_length=50, on_delete=django.db.models.deletion.CASCADE, to='plots_lots.croptype', unique=True, verbose_name='Tipo de cultivo')),
            ],
            options={
                'verbose_name': 'Tarifa de Consumo',
                'verbose_name_plural': 'Tarifas de Consumos',
            },
        ),
    ]
