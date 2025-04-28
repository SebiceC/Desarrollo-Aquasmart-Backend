from django.conf import settings  # Añadir esta línea
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0007_alter_watersupplyfailurereport_lot_and_more'),  # Asegúrate de que la dependencia sea correcta
        ('plots_lots', '0008_croptype_lot_crop_name_alter_lot_crop_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='ApplicationFailureReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('observations', models.CharField(help_text='Detalle del fallo reportado (hasta 200 caracteres)', max_length=200, verbose_name='Observaciones')),
                ('status', models.CharField(choices=[('pendiente', 'Pendiente'), ('resuelto', 'Resuelto')], default='pendiente', max_length=10, verbose_name='Estado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha solicitud')),
                ('reviewed_at', models.DateTimeField(null=True, blank=True, verbose_name='Fecha revisión')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Solicitante')),
            ],
            options={
                'verbose_name': 'Reporte de fallo en el aplicativo',
                'verbose_name_plural': 'Reportes de fallos en el aplicativo',
            },
        ),
    ]
