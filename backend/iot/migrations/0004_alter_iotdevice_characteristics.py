# Generated by Django 5.1.6 on 2025-03-19 06:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iot', '0003_rename_caracteristicas_iotdevice_characteristics_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='iotdevice',
            name='characteristics',
            field=models.CharField(blank=True, default='Sin características', max_length=300, verbose_name='Características del Dispositivo'),
        ),
    ]
