# Generated by Django 5.1.6 on 2025-04-07 16:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('iot', '0010_remove_unique_valve_48'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='devicetype',
            options={'verbose_name': 'Tipo de dispositivo IoT', 'verbose_name_plural': 'Tipos de dispositivos IoT'},
        ),
    ]
