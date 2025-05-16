from rest_framework import permissions

class CanAccessAssignmentView(permissions.BasePermission):
    """
    Permiso global para acceder a cualquier acción del ViewSet.
    El usuario debe tener al menos uno de los permisos requeridos.
    """    
    def has_permission(self, request, view):
        permission_map = {
            'list': 'communication.view_assignment',            
            'create': 'communication.can_assign_user',        
        }
          # Obtener el permiso requerido para la acción actual
        required_permission = permission_map.get(view.action)
          # Si no está definido, denegar por defecto
        if not required_permission:
            return False
        return request.user.has_perm(required_permission)
