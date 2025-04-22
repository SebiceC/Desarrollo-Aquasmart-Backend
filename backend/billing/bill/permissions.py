from rest_framework.permissions import BasePermission

class IsOwnerOrAdmin(BasePermission):
    """
    Permiso personalizado que permite a los administradores ver todas las facturas y a los usuarios ver solo sus propias facturas.
    """
    def has_permission(self, request, view):
        # Verificar si el usuario está autenticado
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Los administradores pueden hacer cualquier acción
        if request.user.is_staff:
            return True

        # Los usuarios no administradores solo pueden ver las facturas si están autenticados
        return True

    def has_object_permission(self, request, view, obj):
        # Los administradores pueden ver cualquier factura
        if request.user.is_staff:
            return True
        
        # Los usuarios solo pueden ver sus propias facturas
        return obj.client == request.user
