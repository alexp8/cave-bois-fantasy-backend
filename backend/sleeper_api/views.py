import requests
from django.http import JsonResponse
from rest_framework.decorators import api_view
from django.conf import settings


def fetch_data_from_sleeper_api(endpoint):
    """
    Helper function to make GET requests to the Sleeper API.

    :param endpoint: The specific API endpoint to hit (e.g., "/players/nfl").
    :return: Response with the JSON data or an error message.
    """
    url = f"{settings.SLEEPER_API_URL}/{endpoint}"
    headers = {"Accept" : "application/json"}
    print(url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": str("Failed getting data")}

@api_view(['GET'])
def get_transactions(league_id, round):
    endpoint = f"league/{league_id}/transactions/{round}"
    return fetch_data_from_sleeper_api(endpoint)

@api_view(['GET'])
def get_users(request, league_id):
    endpoint = f"league/{league_id}/users"
    return JsonResponse(fetch_data_from_sleeper_api(endpoint), safe=False)

@api_view(['GET'])
def get_rosters(league_id):
    endpoint = f"league/{league_id}/rosters"
    return fetch_data_from_sleeper_api(endpoint)

@api_view(['GET'])
def get_matchups(league_id, week):
    endpoint = f"league/{league_id}/transactions/{week}"
    return fetch_data_from_sleeper_api(endpoint)

