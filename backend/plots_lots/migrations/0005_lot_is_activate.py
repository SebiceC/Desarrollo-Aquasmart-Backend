# Generated by Django 5.1.6 on 2025-03-17 16:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plots_lots", "0004_soiltype_alter_plot_is_activate_lot"),
    ]

    operations = [
        migrations.AddField(
            model_name="lot",
            name="is_activate",
            field=models.BooleanField(
                db_index=True,
                default=True,
                help_text="Indica si el lote esta habilitado",
                verbose_name="estado lote",
            ),
        ),
    ]
