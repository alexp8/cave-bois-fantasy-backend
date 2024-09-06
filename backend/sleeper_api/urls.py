from django.urls import path
from .views import get_transactions, get_rosters, get_users, get_matchups

urlpatterns = [
    path('sleeper/transactions/<str:league_id>/<int:round>/', get_transactions, name='get_transactions'),
    path('sleeper/get_rosters/<str:league_id>', get_rosters, name='get_rosters'),
    path('sleeper/get_users/<str:league_id>', get_users, name='get_users'),
    path('sleeper/get_matchups/<str:league_id>/<int:week>/', get_matchups, name='get_matchups'),
]
