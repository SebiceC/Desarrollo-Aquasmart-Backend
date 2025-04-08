from rest_framework import serializers

class HasChangesSerializer(serializers.ModelSerializer):
    """
    Serializer base con método para detectar cambios
    """
    def has_changes(self):
        if not self.instance:
            return True  # Nuevo registro siempre tiene cambios
        
        for field_name, new_value in self.validated_data.items():
            old_value = getattr(self.instance, field_name)
            if old_value != new_value:
                return True
        return False