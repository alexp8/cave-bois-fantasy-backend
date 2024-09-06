from django.urls import path
from .views import get_players_from_sleeper

urlpatterns = [
    path('get_players', get_players_from_sleeper, name='get_players_from_sleeper'),
]
