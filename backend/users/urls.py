from django.urls import path
from .views import CustomUserCreateView, CustomUserListView,UserRegisterAPIView, DocumentTypeView, PersonTypeView, UserInactiveAPIView,UseroProfilelView
from .authentication import GenerateOtpView,ResetPasswordView,ValidateOtpView, LoginView, RefreshTokenView
urlpatterns = [
    path('admin/listed', CustomUserListView.as_view(), name='customuser-list'),  # Listar usuarios
    path('admin/document-type',DocumentTypeView.as_view(), name='document-type'),
    path('admin/person-type', PersonTypeView.as_view(), name='person-type'),
    path("admin/register/<str:document>", UserRegisterAPIView.as_view(), name='customuser-register'),
    path('admin/inactive/<str:document>',UserInactiveAPIView.as_view(),name='Inative-user'),
    path('profile', UseroProfilelView.as_view(), name='perfil-usuario'),
    path('pre-register', CustomUserCreateView.as_view(), name='customuser-pre-register'),  # Pre-registro de usuarios    
    path('login', LoginView.as_view(), name='login'), # Login
    path('token/refresh', RefreshTokenView.as_view(), name='token_refresh'),
    path('generate-otp', GenerateOtpView.as_view(), name='generate_otp'),
    path('validate-otp',ValidateOtpView.as_view(), name='validate-otp'),
    path('reset-password',ResetPasswordView.as_view(), name='reset-password'),
    
]