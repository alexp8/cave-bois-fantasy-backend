import requests
from django.conf import settings

from logger_util import logger


def fetch_data_from_sleeper_api(endpoint):
    """
    Helper function to make GET requests to the Sleeper API.

    :param endpoint: The specific API endpoint to hit (e.g., "/players/nfl").
    :return: Response with the JSON data or an error message.
    """
    url = f"{settings.SLEEPER_API_URL}/{endpoint}"
    headers = {"Accept" : "application/json"}
    logger.debug(url)
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        logger.error(f"Failed hitting API '{endpoint}'\nResponse={str(response)}")
        raise Exception(f"Failed getting data for '{endpoint}': {str(response)}")

def get_transactions(league_id, round):
    endpoint = f"league/{league_id}/transactions/{round}"
    return fetch_data_from_sleeper_api(endpoint)

def get_users(league_id):
    return fetch_data_from_sleeper_api(f"league/{league_id}/users")

def get_players():
    return fetch_data_from_sleeper_api(f"players/nfl")

# https://docs.sleeper.com/#getting-rosters-in-a-league
def get_rosters(league_id):
    return fetch_data_from_sleeper_api(f"league/{league_id}/rosters")

def get_matchups(league_id, week):
    return fetch_data_from_sleeper_api(f"league/{league_id}/transactions/{week}")

def get_league(league_id):
    return fetch_data_from_sleeper_api(f"league/{league_id}")

def get_drafts(league_id):
    return fetch_data_from_sleeper_api(f"league/{league_id}/drafts")

def get_user_info(username):
    return fetch_data_from_sleeper_api(f"user/{username}")

def get_user_leagues(user_id, sport, season):
    return fetch_data_from_sleeper_api(f"user/{user_id}/leagues/{sport}/{season}")

# https://docs.sleeper.com/#get-a-specific-draft
def get_draft_picks(draft_id):
    return fetch_data_from_sleeper_api(f"draft/{draft_id}/picks")

# https://docs.sleeper.com/#get-traded-picks-in-a-draft
def get_traded_draft_picks(draft_id):
    return fetch_data_from_sleeper_api(f"draft/{draft_id}/traded_picks")
