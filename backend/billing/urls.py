from django.urls import path
from .views import RatesAndCompanyView
from .bill.views import UserBillListView, AdminBillListView

urlpatterns = [
    path('rates-company', RatesAndCompanyView.as_view(), name='rates-company'), # Listar y actualizar tarifas y empresa
    path('user/bills', UserBillListView.as_view(), name='user-bills'),  # Facturas de un usuario
    path('admin/bills', AdminBillListView.as_view(), name='admin-bills'),  # Todas las facturas para admin
]