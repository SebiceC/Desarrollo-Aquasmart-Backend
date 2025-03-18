# Generated by Django 5.1.6 on 2025-03-17 16:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plots_lots", "0003_plot_is_activate"),
    ]

    operations = [
        migrations.CreateModel(
            name="SoilType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        max_length=50, unique=True, verbose_name="Tipo de suelo"
                    ),
                ),
            ],
            options={
                "verbose_name": "Tipo de suelo",
                "verbose_name_plural": "Tipos de suelo",
            },
        ),
        migrations.AlterField(
            model_name="plot",
            name="is_activate",
            field=models.BooleanField(
                db_index=True,
                default=True,
                help_text="Indica si el predio esta habilitado",
                verbose_name="estado predio",
            ),
        ),
        migrations.CreateModel(
            name="Lot",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "id_lot",
                    models.CharField(
                        editable=False,
                        max_length=15,
                        unique=True,
                        verbose_name="ID de lote",
                    ),
                ),
                (
                    "crop_type",
                    models.CharField(max_length=20, verbose_name="Tipo de cultivo"),
                ),
                (
                    "crop_variety",
                    models.CharField(
                        blank=True,
                        max_length=20,
                        null=True,
                        verbose_name="Variedad del cultivo",
                    ),
                ),
                (
                    "plot",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lotes",
                        to="plots_lots.plot",
                        verbose_name="Predio",
                    ),
                ),
                (
                    "soil_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="plots_lots.soiltype",
                        verbose_name="Tipo de suelo",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lote",
                "verbose_name_plural": "Lotes",
            },
        ),
    ]
