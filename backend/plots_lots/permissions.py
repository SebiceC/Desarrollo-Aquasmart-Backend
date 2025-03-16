from rest_framework.permissions import BasePermission

class IsAdminUser(BasePermission):
    """
    Permiso personalizado para permitir solo a usuarios administradores.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_staff)

class IsOwnerOrAdmin(BasePermission):
    """
    Permiso personalizado para permitir a usuarios ver solo sus propios predios,
    mientras que los administradores pueden ver todos.
    """
    def has_permission(self, request, view):
        # Si es una lista (GET al endpoint principal), solo permitir a admins
        if view.action == 'list':
            return bool(request.user and request.user.is_staff)
        # Para otras acciones, permitir si el usuario está autenticado
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Permitir acceso si el usuario es admin o es el dueño del predio
        return bool(
            request.user.is_staff or
            obj.owner.document == request.user.document
        )
