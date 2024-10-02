import logging

import requests
from django.conf import settings

# Use the logger from the global settings
logger = logging.getLogger('django')

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
        logger.error(str(response))
        raise Exception(f"Failed getting data: {str(response)}")

def get_transactions(league_id, round):
    endpoint = f"league/{league_id}/transactions/{round}"
    return fetch_data_from_sleeper_api(endpoint)

def get_users(league_id):
    return fetch_data_from_sleeper_api(f"league/{league_id}/users")

def get_players():
    return fetch_data_from_sleeper_api(f"players/nfl")

def get_rosters(league_id):
    return fetch_data_from_sleeper_api(f"league/{league_id}/rosters")

def get_matchups(league_id, week):
    return fetch_data_from_sleeper_api(f"league/{league_id}/transactions/{week}")

def get_league(league_id):
    return fetch_data_from_sleeper_api(f"league/{league_id}")

def get_draft(league_id):
    return fetch_data_from_sleeper_api(f"league/{league_id}/drafts")
