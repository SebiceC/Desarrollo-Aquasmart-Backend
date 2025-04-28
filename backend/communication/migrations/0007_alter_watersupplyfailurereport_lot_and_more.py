
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0006_alter_watersupplyfailurereport_lot_and_more'),
        ('plots_lots', '0008_croptype_lot_crop_name_alter_lot_crop_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='watersupplyfailurereport',
            name='lot',
            field=models.ForeignKey(blank=True, help_text='Lote al que se le solicita el cambio de caudal', null=True, on_delete=django.db.models.deletion.CASCADE, to='plots_lots.lot', verbose_name='Lote'),
        ),
        migrations.AlterField(
            model_name='watersupplyfailurereport',
            name='plot',
            field=models.ForeignKey(blank=True, help_text='Predio de la válvula principal (si es válvula principal de predio)', null=True, on_delete=django.db.models.deletion.CASCADE, to='plots_lots.plot', verbose_name='Predio'),
        ),
    ]
