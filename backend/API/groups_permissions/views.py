# views.py
from rest_framework import viewsets, status
from rest_framework import serializers
from rest_framework.response import Response
from django.contrib.auth.models import Group, Permission
from .serializers import GroupSerializer, PermissionSerializer
from rest_framework.views import APIView
from collections import defaultdict

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def assign_permissions(self, request, pk=None):
        group = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        
        # Obtener los permisos
        permissions = Permission.objects.filter(id__in=permission_ids)
        
        # Filtrar permisos que ya están asignados al grupo
        existing_permissions = group.permissions.filter(id__in=permission_ids)
        new_permissions = permissions.exclude(id__in=existing_permissions.values_list('id', flat=True))
        
        # Si hay permisos duplicados, devolver un mensaje indicando cuáles ya existen
        if existing_permissions.exists():
            existing_permissions_data = PermissionSerializer(existing_permissions, many=True).data
            return Response({
                "detail": "Algunos permisos ya están asignados al grupo.",
                "existing_permissions": existing_permissions_data,
                "new_permissions_added": new_permissions.count()
            }, status=status.HTTP_200_OK)
        
        # Agregar solo los permisos nuevos
        group.permissions.add(*new_permissions)
        
        return Response({
            "detail": "Permisos asignados correctamente.",
            "new_permissions_added": new_permissions.count()
        }, status=status.HTTP_200_OK)

    def remove_permissions(self, request, pk=None):
        group = self.get_object()
        permission_ids = request.data.get('permission_ids', [])
        
        # Obtener los permisos
        permissions = Permission.objects.filter(id__in=permission_ids)
        
        # Quitar permisos del grupo
        group.permissions.remove(*permissions)
        
        return Response({"detail": "Permisos quitados correctamente."}, status=status.HTTP_200_OK)

class PermissionListView(APIView):
    """
    Listar todos los permisos disponibles.
    """
    def get(self, request):
        permissions = Permission.objects.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)
    
class PermissionSerializer(serializers.ModelSerializer):
    app_label = serializers.CharField(source='content_type.app_label', read_only=True)
    model = serializers.CharField(source='content_type.model', read_only=True)

    class Meta:
        model = Permission
        fields = ['id', 'codename', 'name', 'app_label', 'model']
class GroupPermissionsView(APIView):
    """
    Listar los permisos de un grupo específico.
    """
    def get(self, request, pk=None):
        group = Group.objects.get(pk=pk)
        permissions = group.permissions.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)
    
class GroupedPermissionsView(APIView):
    """
    Listar permisos agrupados por app y modelo, similar al panel de Django.
    """
    def get(self, request):
        permissions = Permission.objects.all().select_related('content_type')
        grouped_permissions = defaultdict(lambda: defaultdict(list))

        # Agrupar permisos por app y modelo
        for perm in permissions:
            app_label = perm.content_type.app_label
            model = perm.content_type.model
            grouped_permissions[app_label][model].append({
                'id': perm.id,
                'codename': perm.codename,
                'name': perm.name,
            })

        return Response(grouped_permissions)    