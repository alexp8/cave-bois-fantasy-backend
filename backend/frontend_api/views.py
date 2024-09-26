from django.http import JsonResponse
from rest_framework.decorators import api_view
from sleeper_api.sleeper_api_svc import get_players, get_transactions, get_league
import json
import os

PLAYERS_JSON_FILE = 'sleeper_api/sleeper_data/get_players.json'
DRAFT_PICKS_JSON_FILE = 'sleeper_api/sleeper_data/draft_picks.json'

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
        players_data = get_players
        with open(PLAYERS_JSON_FILE, 'w') as json_file:
            json.dump(players_data, json_file, indent=4)
    else:
        players_data = load_json(PLAYERS_JSON_FILE)
    filtered_data = [{"first_name": item["first_name"], "last_name": item["last_name"]} for item in players_data.values()]
    return JsonResponse(filtered_data, safe=False)


def load_json(json_file_path):
    with open(json_file_path, 'r') as file:
        return json.load(file)

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

    # read in player and draft pick data
    raw_players_data = load_json(PLAYERS_JSON_FILE)
    draft_picks = load_json(DRAFT_PICKS_JSON_FILE)

    player_names_arr = [
        f"{item['first_name']} {item['last_name']}"
        for item in raw_players_data.values()
        if 'first_name' in item and 'last_name' in item
    ]

    # apply search
    filtered_data = [
        name
        for name in player_names_arr
        if search_str.lower() in name.lower()
    ][:10]

    # search for draft picks
    filtered_data += [
        draft_pick
        for draft_pick in draft_picks
        if search_str.lower() in draft_pick.lower()
    ][:(10 - len(filtered_data))]

    # return up to 10 results
    return JsonResponse(filtered_data, safe=False)

    # TODO a smart filter that puts most 'relevant' players on top

@api_view(['GET'])
def get_league_trades(request, sleeper_league_id):

    all_transactions = []
    all_league_ids = [sleeper_league_id]

    # get previous_league_ids
    previous_league_id = None
    while True:
        if previous_league_id:
            league_data = get_league(previous_league_id)
        else:
            league_data = get_league(sleeper_league_id)

        previous_league_id = league_data['previous_league_id']
        if not previous_league_id:
            break
        all_league_ids.append(previous_league_id)

    # get trades from entire league history
    for league_id in all_league_ids:
        for i in range(21):

            # store previous years trade data, to prevent unnecessary API calls
            transactions_data = None
            file_path = f'sleeper_data/{league_id}_league_data.json'
            if league_id != sleeper_league_id and os.path.exists(file_path):
                transactions_data = load_json(file_path)
            else:
                transactions_data = get_transactions("players/nfl", league_id)
                transactions_data = [item for item in transactions_data if item.get('type') == 'trade' and item.get('status') == 'complete']

                if not transactions_data or len(transactions_data) == 0:
                    continue

                # store transaction json data of previous years
                if league_id != sleeper_league_id:
                    with open(file_path, 'w') as json_file:
                        json.dump(transactions_data, json_file, indent=4) # TODO store in DB?

            all_transactions.append(transactions_data)

    return all_transactions
