from django.urls import path
from . import views

urlpatterns = [
    path('api/external/', views.external_api_view, name='external-api'),
]