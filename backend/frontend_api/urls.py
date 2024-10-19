from django.urls import path

from .views import get_league_trades, get_version, get_trade, get_leagues

urlpatterns = [
    # path('get_players_like/<str:search_str>', get_players_from_sleeper_like, name='get_players_from_sleeper_like'),
    path('get_league_trades/<str:sleeper_league_id>', get_league_trades, name='get_league_trades'),
    path('get_trade/<str:transaction_id>', get_trade, name='get_trade'),
    path('get_leagues/<str:user_name>', get_leagues, name='get_leagues'),
    path('version', get_version, name='get_version'),
]
