from rest_framework import serializers
from django.contrib.auth.models import Group, Permission



class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)
    model = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name', 'app_label', 'model']        

class GroupSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'permissions']

class GroupPermissionSerializer(serializers.ModelSerializer):
    group_name = serializers.SerializerMethodField()

    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name', 'content_type', 'group_name']

    def get_group_name(self, obj):
        # Obtener el nombre del grupo al que pertenece el permiso
        groups = obj.group_set.all()
        if groups:
            return groups[0].name  # Suponemos que un permiso pertenece a un solo grupo
        return None        