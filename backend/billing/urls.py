from django.urls import path
from .views import RatesAndCompanyView

urlpatterns = [
    path('rates-company', RatesAndCompanyView.as_view(), name='rates-company'),
]