# views.py
from rest_framework import viewsets, status
from rest_framework import serializers
from rest_framework.response import Response
from django.contrib.auth.models import Group, Permission
from .serializers import (
    GroupSerializer,
    PermissionSerializer,
    GroupPermissionSerializer,
)
from rest_framework.views import APIView
from collections import defaultdict
from users.models import CustomUser
from rest_framework.permissions import IsAdminUser, IsAuthenticated


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    permission_classes = [IsAdminUser, IsAuthenticated]

    def assign_permissions(self, request, pk=None):
        group = self.get_object()
        permission_ids = request.data.get("permission_ids", [])

        # Obtener los permisos
        permissions = Permission.objects.filter(id__in=permission_ids)

        # Filtrar permisos que ya están asignados al grupo
        existing_permissions = group.permissions.filter(id__in=permission_ids)
        new_permissions = permissions.exclude(
            id__in=existing_permissions.values_list("id", flat=True)
        )

        # Si hay permisos duplicados, devolver un mensaje indicando cuáles ya existen
        if existing_permissions.exists():
            existing_permissions_data = PermissionSerializer(
                existing_permissions, many=True
            ).data
            return Response(
                {
                    "detail": "Algunos permisos ya están asignados al grupo.",
                    "existing_permissions": existing_permissions_data,
                    "new_permissions_added": new_permissions.count(),
                },
                status=status.HTTP_200_OK,
            )

        # Agregar solo los permisos nuevos
        group.permissions.add(*new_permissions)

        return Response(
            {
                "detail": "Permisos asignados correctamente.",
                "new_permissions_added": new_permissions.count(),
            },
            status=status.HTTP_200_OK,
        )

    def remove_permissions(self, request, pk=None):
        group = self.get_object()
        permission_ids = request.data.get("permission_ids", [])

        # Obtener los permisos
        permissions = Permission.objects.filter(id__in=permission_ids)

        # Quitar permisos del grupo
        group.permissions.remove(*permissions)

        return Response(
            {"detail": "Permisos quitados correctamente."}, status=status.HTTP_200_OK
        )


class PermissionListView(APIView):
    """
    Listar todos los permisos disponibles.
    """

    permission_classes = [IsAdminUser, IsAuthenticated]

    def get(self, request):
        permissions = Permission.objects.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)


class GroupPermissionsView(APIView):
    """
    Listar los permisos de un grupo específico.
    """

    permission_classes = [IsAdminUser, IsAuthenticated]

    def get(self, request, pk=None):
        group = Group.objects.get(pk=pk)
        permissions = group.permissions.all()
        serializer = PermissionSerializer(permissions, many=True)
        return Response(serializer.data)


class GroupedPermissionsView(APIView):
    """
    Listar permisos agrupados por app y modelo, similar al panel de Django.
    """

    permission_classes = [IsAdminUser, IsAuthenticated]

    def get(self, request):
        permissions = Permission.objects.all().select_related("content_type")
        grouped_permissions = defaultdict(lambda: defaultdict(list))

        # Agrupar permisos por app y modelo
        for perm in permissions:
            app_label = perm.content_type.app_label
            model = perm.content_type.model
            grouped_permissions[app_label][model].append(
                {
                    "id": perm.id,
                    "codename": perm.codename,
                    "name": perm.name,
                }
            )

        return Response(grouped_permissions)


class UserPermissionsView(APIView):
    """
    Obtener los permisos de un usuario agrupados por grupo.
    """

    permission_classes = [IsAdminUser, IsAuthenticated]

    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(document=user_id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Usuario no encontrado."}, status=404)

        # Permisos directos del usuario
        direct_permissions = user.user_permissions.all()
        direct_permissions_data = GroupPermissionSerializer(
            direct_permissions, many=True
        ).data

        # Obtener los grupos a los que pertenece el usuario
        groups = user.groups.all()

        # Diccionario para agrupar permisos por nombre de grupo
        grouped_permissions = {}

        for group in groups:
            # Obtener los permisos del grupo
            permissions = group.permissions.all()
            # Serializar los permisos
            permissions_data = GroupPermissionSerializer(permissions, many=True).data
            # Agregar al diccionario
            grouped_permissions[group.name] = permissions_data

        return Response(
            {
                "Permisos_Usuario": direct_permissions_data,
                "Permisos_Rol": grouped_permissions,
            }
        )


class AddUserPermissionsView(APIView):
    """
    Agregar permisos directamente a un usuario.
    """

    permission_classes = [IsAdminUser, IsAuthenticated]

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(document=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        # Validar que el campo 'permission_ids' esté presente
        if "permission_ids" not in request.data:
            return Response(
                {"detail": "El campo 'permission_ids' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        permission_ids = request.data.get("permission_ids", [])

        # Validar que los permisos existan
        permissions = Permission.objects.filter(id__in=permission_ids)
        if len(permissions) != len(permission_ids):
            return Response(
                {"detail": "Algunos permisos no existen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar si los permisos ya están asignados al usuario
        existing_permissions = user.user_permissions.filter(id__in=permission_ids)
        if existing_permissions.exists():
            existing_permissions_data = PermissionSerializer(
                existing_permissions, many=True
            ).data
            return Response(
                {
                    "detail": "Algunos permisos ya están asignados al usuario.",
                    "existing_permissions": existing_permissions_data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Agregar permisos al usuario
        user.user_permissions.add(*permissions)

        return Response(
            {"detail": "Permisos agregados correctamente."}, status=status.HTTP_200_OK
        )


class RemoveUserPermissionsView(APIView):
    """
    Remover permisos directamente de un usuario.
    """

    permission_classes = [IsAdminUser, IsAuthenticated]

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(document=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        # Validar que el campo 'permission_ids' esté presente
        if "permission_ids" not in request.data:
            return Response(
                {"detail": "El campo 'permission_ids' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        permission_ids = request.data.get("permission_ids", [])

        # Validar que los permisos existan
        permissions = Permission.objects.filter(id__in=permission_ids)
        if len(permissions) != len(permission_ids):
            return Response(
                {"detail": "Algunos permisos no existen."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verificar si los permisos no están asignados al usuario
        non_existing_permissions = permissions.exclude(
            id__in=user.user_permissions.values_list("id", flat=True)
        )
        if non_existing_permissions.exists():
            non_existing_permissions_data = PermissionSerializer(
                non_existing_permissions, many=True
            ).data
            return Response(
                {
                    "detail": "Algunos permisos no están asignados al usuario.",
                    "non_existing_permissions": non_existing_permissions_data,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Remover permisos del usuario
        user.user_permissions.remove(*permissions)

        return Response(
            {"detail": "Permisos removidos correctamente."}, status=status.HTTP_200_OK
        )


class AssignGroupToUserView(APIView):
    """
    Asignar un grupo a un usuario.
    """

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(document=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        group_id = request.data.get("group_id")
        if not group_id:
            return Response(
                {"detail": "El campo 'group_id' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response(
                {"detail": "Grupo no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        # Asignar el grupo al usuario
        user.groups.add(group)

        return Response(
            {
                "detail": f"Grupo '{group.name}' asignado al usuario '{user.first_name}' correctamente."
            },
            status=status.HTTP_200_OK,
        )


class RemoveGroupFromUserView(APIView):
    """
    Quitar un grupo de un usuario.
    """

    def post(self, request, user_id):
        try:
            user = CustomUser.objects.get(document=user_id)
        except CustomUser.DoesNotExist:
            return Response(
                {"detail": "Usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        group_id = request.data.get("group_id")
        if not group_id:
            return Response(
                {"detail": "El campo 'group_id' es requerido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            group = Group.objects.get(id=group_id)
        except Group.DoesNotExist:
            return Response(
                {"detail": "Grupo no encontrado."}, status=status.HTTP_404_NOT_FOUND
            )

        # Quitar el grupo del usuario
        user.groups.remove(group)

        return Response(
            {
                "detail": f"Grupo '{group.name}' quitado del usuario '{user.first_name}' correctamente."
            },
            status=status.HTTP_200_OK,
        )
