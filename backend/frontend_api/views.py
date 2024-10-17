from django.http import JsonResponse
from rest_framework.decorators import api_view

from fantasy_trades_app.settings import VERSION
from frontend_api.api_helpers import get_trades_api


@api_view(['GET'])
def get_players_from_sleeper(request):
    None


@api_view(['GET'])
def get_players_from_sleeper_like(request, search_str):
    None


@api_view(['GET'])
def get_version(request):
    return JsonResponse({"version": VERSION}, safe=False)


@api_view(['GET'])
def get_league_trades(request, sleeper_league_id):

    roster_id = request.GET.get('rosterId', None)

    return get_trades_api.get_trades(request, sleeper_league_id, roster_id)