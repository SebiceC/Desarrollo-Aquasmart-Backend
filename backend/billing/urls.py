from django.urls import path
from .views import RatesAndCompanyView
from .bill.views import BillListView, BillDetailView,generate_monthly_bills

urlpatterns = [
    path('rates-company', RatesAndCompanyView.as_view(), name='rates-company'), # Listar y actualizar tarifas y empresa
    path('bills', BillListView.as_view(), name='bills'),  # Listar facturas 
    path('bills/<int:pk>', BillDetailView.as_view(), name='bill-detail'),  # Ver detalle de factura 
    path('generate-bills', generate_monthly_bills, name='generate_monthly_bills'),

]