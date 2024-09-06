from django.http import JsonResponse
from rest_framework.decorators import api_view
from sleeper_api.views import fetch_data_from_sleeper_api

@api_view(['GET'])
def get_players_from_sleeper(request):
    players_data = fetch_data_from_sleeper_api("players/nfl")
    return JsonResponse(players_data, safe=False)
