import requests
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings

def fetch_data_from_sleeper_api(endpoint):
    """
    Helper function to make GET requests to the Sleeper API.

    :param endpoint: The specific API endpoint to hit (e.g., "/players/nfl").
    :return: Response with the JSON data or an error message.
    """
    url = f"{settings.SLEEPER_API_URL}/{endpoint}"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        return Response(response.json())  # Return the JSON data if the request is successful
    except requests.exceptions.RequestException as e:
        return Response({"error": str(e)}, status=response.status_code if response else 500)

@api_view(['GET'])
def get_players(request):
    return fetch_data_from_sleeper_api("players/nfl")

@api_view(['GET'])
def get_transactions(request, league_id, round):
    endpoint = f"league/{league_id}/transactions/{round}"
    return fetch_data_from_sleeper_api(endpoint)

@api_view(['GET'])
def get_users(request, league_id):
    endpoint = f"league/{league_id}/users"
    return fetch_data_from_sleeper_api(endpoint)

@api_view(['GET'])
def get_rosters(request, league_id):
    endpoint = f"league/{league_id}/rosters"
    return fetch_data_from_sleeper_api(endpoint)

@api_view(['GET'])
def get_matchups(request, league_id, week):
    endpoint = f"league/{league_id}/transactions/{week}"
    return fetch_data_from_sleeper_api(endpoint)

