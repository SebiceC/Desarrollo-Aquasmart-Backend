from rest_framework.permissions import BasePermission, IsAdminUser

class IsOwnerOrAdmin(BasePermission):
    """
    Permiso personalizado que:
    1. Para acciones de lista (GET /plots o /lots):
       - Permite acceso a administradores para ver todo
       - Permite a usuarios ver sus propios recursos
    2. Para acciones de lectura (GET):
       - Permite acceso a administradores
       - Permite acceso a dueños para ver sus propios recursos
    3. Para acciones de escritura (POST, PUT, PATCH, DELETE):
       - Permite acceso solo a administradores
    """
    def has_permission(self, request, view):
        # Verificar autenticación básica
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Para acciones de escritura, solo admins
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            return IsAdminUser().has_permission(request, view)
            
        # Para acciones de lectura (incluyendo list), permitir usuarios autenticados
        return True

    def has_object_permission(self, request, view, obj):
        # Para acciones de escritura, solo admins
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            return IsAdminUser().has_permission(request, view)
            
        # Para acciones de lectura
        if IsAdminUser().has_permission(request, view):
            return True
            
        # Para lotes, verificar el dueño del predio asociado
        if hasattr(obj, 'plot'):
            return obj.plot.owner.document == request.user.document
            
        # Para predios, verificar el dueño directamente
        return obj.owner.document == request.user.document
