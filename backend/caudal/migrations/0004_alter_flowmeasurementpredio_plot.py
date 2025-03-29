# Generated by Django 5.1.6 on 2025-03-24 04:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("caudal", "0003_flowinconsistency_flowmeasurementlote_and_more"),
        ("plots_lots", "0007_alter_plot_plot_extension"),
    ]

    operations = [
        migrations.AlterField(
            model_name="flowmeasurementpredio",
            name="plot",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="flow_measurements_predio",
                to="plots_lots.plot",
                verbose_name="Predio",
            ),
        ),
    ]
