# Generated by Django 5.1.6 on 2025-03-20 18:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iot', '0007_alter_iotdevice_id_lot_alter_iotdevice_id_plot'),
    ]

    operations = [
        migrations.AddField(
            model_name='iotdevice',
            name='owner_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
