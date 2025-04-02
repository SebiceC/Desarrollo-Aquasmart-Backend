from django.urls import path
from .views import ServoControlAPI  

urlpatterns = [
    path('', ServoControlAPI.as_view(), name='servo-control'),
]