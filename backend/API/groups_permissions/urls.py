from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import GroupViewSet, PermissionListView, GroupPermissionsView, GroupedPermissionsView,UserPermissionsView,AddUserPermissionsView, RemoveUserPermissionsView, AssignGroupToUserView, RemoveGroupFromUserView

router = DefaultRouter()


urlpatterns = [
    #Grupos(Roles)
        # Endpoint para listar grupo
    path('groups',GroupViewSet.as_view({'get': 'list','post':'create'})),
        # Endpoint para asignar permisos a un grupo
    path('groups/<int:pk>/assign_permissions', GroupViewSet.as_view({'post': 'assign_permissions'}), name='assign-permissions'),
        # Endpoint para quitar permisos de un grupo
    path('groups/<int:pk>/remove_permissions', GroupViewSet.as_view({'post': 'remove_permissions'}), name='remove-permissions'),   
        # Endpoint para ver los permisos de un grupo específico
    path('groups/<int:pk>/permissions', GroupPermissionsView.as_view(), name='group-permissions'),
    path('groups/delete/<int:pk>',GroupViewSet.as_view({'delete': 'destroy'}), name='group-delete'),
    
    
    #Permisos
        # Endpoint para listar todos los permisos disponibles
    path('permissions', PermissionListView.as_view(), name='permission-list'),
        # Endpoint para ver los permisos agrupados
    path('grouped_permissions', GroupedPermissionsView.as_view(), name='grouped-permissions'),
    
    #Usuarios    
        # Endpoint para ver los permisos de un usuario
    path('users/<int:user_id>/permissions', UserPermissionsView.as_view(), name='user-permissions'),
        # Agregar permisos a un usuario
    path('users/<int:user_id>/add_permissions', AddUserPermissionsView.as_view(), name='add-user-permissions'),
        # Remover permisos de un usuario
    path('users/<int:user_id>/remove_permission', RemoveUserPermissionsView.as_view(), name='remove-user-permissions'),
        # Endpoint para darle un grupo(rol) a un usuario
    path('users/<int:user_id>/assign_group', AssignGroupToUserView.as_view(), name='assign-group-to-user'),
        # Endpoint para remover un grupo(rol) a un usuario
    path('users/<int:user_id>/remove_group', RemoveGroupFromUserView.as_view(), name='remove-group-from-user'),

]
