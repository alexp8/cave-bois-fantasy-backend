from django.urls import path

from .views import get_league_trades, get_version, get_trade, get_leagues, get_leaderboard, submit_feedback, get_feedback

urlpatterns = [
    path('get_league_trades/<str:sleeper_league_id>', get_league_trades, name='get_league_trades'),
    path('get_trade/<str:transaction_id>', get_trade, name='get_trade'),
    path('get_leagues/<str:user_name>', get_leagues, name='get_leagues'),
    path('version', get_version, name='get_version'),
    path('get_leaderboard/<str:sleeper_league_id>', get_leaderboard, name='get_leaderboard'),
    path('submit_feedback', submit_feedback, name='submit_feedback'),
    path('get_feedback', get_feedback, name='get_feedback'),
]
