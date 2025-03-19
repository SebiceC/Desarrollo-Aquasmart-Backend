from rest_framework import serializers
from .models import Plot, Lot, SoilType
from users.models import CustomUser

class PlotSerializer(serializers.ModelSerializer):
    """Serializer base para predios con campos básicos."""
    owner = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.all(),
        error_messages={'does_not_exist': "El usuario asignado no está registrado"}
    )

    class Meta:
        model = Plot
        fields = ['id_plot', 'owner', 'plot_name', 'latitud', 'longitud', 'plot_extension', 'registration_date', 'is_activate']
        read_only_fields = ['id_plot', 'registration_date', 'is_activate']

    def validate(self, data):
        """Validación personalizada para evitar duplicados en la georeferenciación."""
        latitud = data.get('latitud')
        longitud = data.get('longitud')

        instance = self.instance
        if Plot.objects.exclude(id_plot=instance.id_plot if instance else None).filter(latitud=latitud, longitud=longitud).exists():
            raise serializers.ValidationError("La georeferenciación ya está asignada a otro predio.")
        return data

class LotSerializer(serializers.ModelSerializer):
    """Serializer base para lotes con campos básicos."""
    class Meta:
        model = Lot
        fields = ['id_lot', 'plot', 'crop_type', 'crop_variety', 'soil_type', 'is_activate', 'registration_date']
        read_only_fields = ['id_lot', 'registration_date', 'is_activate']

    def validate_plot(self, value):
        """Valida que el predio exista y esté activo."""
        if not Plot.objects.filter(id_plot=value.id_plot, is_activate=True).exists():
            raise serializers.ValidationError("El predio no existe o está inactivo.")
        return value

    def validate_soil_type(self, value):
        """Valida que el tipo de suelo exista."""
        if not SoilType.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("El tipo de suelo no existe.")
        return value

class PlotDetailSerializer(PlotSerializer):
    """Serializer extendido para ver detalles de predios, incluyendo sus lotes."""
    lotes = LotSerializer(many=True, read_only=True, source='lot_set')
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)

    class Meta(PlotSerializer.Meta):
        fields = PlotSerializer.Meta.fields + ['lotes', 'owner_name']

class LotDetailSerializer(LotSerializer):
    """Serializer extendido para ver detalles de lotes, incluyendo información del predio."""
    plot_name = serializers.CharField(source='plot.plot_name', read_only=True)
    plot_owner = serializers.CharField(source='plot.owner.get_full_name', read_only=True)
    soil_type_name = serializers.CharField(source='soil_type.name', read_only=True)

    class Meta(LotSerializer.Meta):
        fields = LotSerializer.Meta.fields + ['plot_name', 'plot_owner', 'soil_type_name']

class SoilTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilType
        fields = ['id', 'name']        