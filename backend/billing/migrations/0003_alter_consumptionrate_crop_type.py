# Generated by Django 5.1.6 on 2025-04-07 22:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0002_alter_company_options_alter_consumptionrate_options_and_more'),
        ('plots_lots', '0008_croptype_lot_crop_name_alter_lot_crop_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='consumptionrate',
            name='crop_type',
            field=models.OneToOneField(help_text='Tipo de cultivo (e.j., Agricultura, Psicultura)', on_delete=django.db.models.deletion.CASCADE, to='plots_lots.croptype', verbose_name='Tipo de cultivo'),
        ),
    ]
