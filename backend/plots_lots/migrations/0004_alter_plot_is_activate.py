# Generated by Django 5.1.6 on 2025-03-17 12:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plots_lots', '0003_plot_is_activate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='plot',
            name='is_activate',
            field=models.BooleanField(db_index=True, default=True, help_text='Indica si el predio esta habilitado', verbose_name='estado predio'),
        ),
    ]
