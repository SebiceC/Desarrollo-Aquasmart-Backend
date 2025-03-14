# Generated by Django 5.1.6 on 2025-03-04 11:32

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0007_merge_20250304_1131"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="document_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="users_with_document_type",
                to="users.documenttype",
                verbose_name="Tipo de Documento",
            ),
        ),
        migrations.AlterField(
            model_name="customuser",
            name="person_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="users_with_person_type",
                to="users.persontype",
                verbose_name="Tipo de Persona",
            ),
        ),
    ]
