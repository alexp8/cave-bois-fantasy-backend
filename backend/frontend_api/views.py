from django.http import JsonResponse
from rest_framework.decorators import api_view
from sleeper_api.views import fetch_data_from_sleeper_api
import json

PLAYERS_JSON_FILE = 'sleeper_api/sleeper_data/get_players.json'

@api_view(['GET'])
def get_players_from_sleeper(request):
    """
        Fetches or reads player data from Sleeper API or local storage and returns a filtered list of players.

        If `force_refresh` is True, data will be fetched from the Sleeper API. Otherwise, data will be read from local storage.

        Checks for presence of optional parameter:
        force_refresh (bool): A flag to determine whether to fetch fresh data from Sleeper API or use cached data.

        Args:
            request (HttpRequest): The HTTP request object, automatically passed by Django REST framework.

        Returns:
            JsonResponse: A JSON response containing a list of filtered player data with 'first_name' and 'last_name' keys.

        Example:
            >>> get_players_from_sleeper(request, False)
            JsonResponse([
                {"first_name": "Patrick", "last_name": "Mahomes"},
                {"first_name": "Josh", "last_name": "Allen"},
            ])
        """

    # force refresh players
    force_refresh = request.GET.get('force_refresh', 'False').lower() == 'true'

    if force_refresh is True:
        print('fresh')
        players_data = fetch_data_from_sleeper_api("players/nfl")
        with open(PLAYERS_JSON_FILE, 'w') as json_file:
            json.dump(players_data, json_file, indent=4)
    else:
        print('cached players')
        players_data = read_players()
    filtered_data = [{"first_name": item["first_name"], "last_name": item["last_name"]} for item in players_data.values()]
    return JsonResponse(filtered_data, safe=False)


def read_players():
    with open(PLAYERS_JSON_FILE, 'r') as file:
        players_data = json.load(file)
    return players_data


@api_view(['GET'])
def get_players_from_sleeper_like(request, search_str):
    """
        Filters players based on the given search string for first or last name.

        Args:
            request: http request
            search_str (str): The string to search for in the player's first or last name. The search is case-insensitive.

        Returns:
            list[dict]: A list of players containing 'first_name' and 'last_name' fields
            from the filtered players, limited to 10 results.

        Example:
            >>> get_players_from_sleeper_like(request, 'john')
            [{'first_name': 'John', 'last_name': 'Doe'}, {'first_name': 'Johnathan', 'last_name': 'Smith'}]
        """

    players_data = read_players()
    filtered_data = [
        {"first_name": item["first_name"], "last_name": item["last_name"]}
        for item in players_data.values()
        if search_str.lower() in item["first_name"].lower() or search_str.lower() in item["last_name"].lower()
    ][:10]

    return JsonResponse(filtered_data, safe=False)

