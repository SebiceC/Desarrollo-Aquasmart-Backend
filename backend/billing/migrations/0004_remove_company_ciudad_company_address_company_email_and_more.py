# Generated by Django 5.1.6 on 2025-04-14 22:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0003_alter_consumptionrate_crop_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='company',
            name='ciudad',
        ),
        migrations.AddField(
            model_name='company',
            name='address',
            field=models.CharField(blank=True, max_length=35, null=True),
        ),
        migrations.AddField(
            model_name='company',
            name='email',
            field=models.EmailField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='company',
            name='phone',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
