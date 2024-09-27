from django.urls import path
from .views import get_players_from_sleeper, get_players_from_sleeper_like, get_league_trades

urlpatterns = [
    path('get_players', get_players_from_sleeper, name='get_players_from_sleeper'),
    # path('get_players_like/<str:search_str>', get_players_from_sleeper_like, name='get_players_from_sleeper_like'),
    path('get_league_trades/<str:sleeper_league_id>', get_league_trades, name='get_league_trades'),
]
