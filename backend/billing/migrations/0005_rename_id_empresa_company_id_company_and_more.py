# Generated by Django 5.1.6 on 2025-04-15 14:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0004_remove_company_ciudad_company_address_company_email_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='company',
            old_name='id_empresa',
            new_name='id_company',
        ),
        migrations.RenameField(
            model_name='company',
            old_name='nombre',
            new_name='name',
        ),
    ]
