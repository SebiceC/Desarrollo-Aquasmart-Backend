from django.urls import path
from .views import CustomUserCreateView, CustomUserListView,UserRegisterAPIView, DocumentTypeView, PersonTypeView, UserInactiveAPIView,UserProfilelView,DocumentTypeListView,PersonTypeListView, AdminUserUpdateAPIView, UserProfileUpdateView, UserActivateAPIView, AssignPermissionToUser, RemovePermissionFromUser, ListUserPermissions
from .authentication import GenerateOtpPasswordRecoveryView,ResetPasswordView,ValidateOtpView, LoginView, LogoutView, ValidateTokenView, ChangePasswordView


urlpatterns = [
    path('admin/listed', CustomUserListView.as_view(), name='customuser-list'),  # Listar usuarios
    path('admin/document-type',DocumentTypeView.as_view(), name='document-type'),
    path('admin/person-type', PersonTypeView.as_view(), name='person-type'),
    path("admin/register/<str:document>", UserRegisterAPIView.as_view(), name='customuser-register'),
    path('admin/inactive/<str:document>',UserInactiveAPIView.as_view(),name='Inative-user'),
    path('admin/activate/<str:document>',UserActivateAPIView.as_view(),name='Activate-user'),
    path('profile', UserProfilelView.as_view(), name='perfil-usuario'),
    path('pre-register', CustomUserCreateView.as_view(), name='customuser-pre-register'),  # Pre-registro de usuarios    
    path('login', LoginView.as_view(), name='login'), # Login
    path('generate-otp-login',GenerateOtpLoginView.as_view(), name='generate_otp_login_agin'),
    path('generate-otp', GenerateOtpPasswordRecoveryView.as_view(), name='generate_otp_password_recovery'),
    path('validate-otp',ValidateOtpView.as_view(), name='validate-otp'),
    path('reset-password',ResetPasswordView.as_view(), name='reset-password'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('validate-token', ValidateTokenView.as_view(), name='validate-token'),
    path('list-document-type',DocumentTypeListView.as_view(), name='listed-document-type'),
    path('list-person-type',PersonTypeListView.as_view(),name='listed-person-type'),
    path('change-password', ChangePasswordView.as_view(), name='change-password'),
    path('admin/update/<str:document>', AdminUserUpdateAPIView.as_view(), name='admin-user-update'),
    path('profile/update',UserProfileUpdateView.as_view(), name='profile-update'),
    path('custom-permissions/assign/', AssignPermissionToUser.as_view(), name='assign-permission'),
    path('custom-permissions/remove/', RemovePermissionFromUser.as_view(), name='remove-permission'),
    path('custom-permissions/user/<str:document>/', ListUserPermissions.as_view(), name='user-permissions'),
]