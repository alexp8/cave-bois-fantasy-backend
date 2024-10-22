import json

from django.core.cache import cache
from frontend_api.cache.constants import CACHE_DURATION, LEAGUE_DATA_CACHE_KEY
from sleeper_api import sleeper_api_svc

def fetch_and_cache_league_data(sleeper_league_id: str, cache_key: str) -> json:
    league_data = sleeper_api_svc.get_league(sleeper_league_id)
    if not league_data:
        raise Exception(f"No data found for sleeper_league_id {sleeper_league_id}")
    cache.set(cache_key, league_data, timeout=CACHE_DURATION)
    return league_data


def get_league_data(sleeper_league_id: str) -> json:
    league_cache_key = f'{LEAGUE_DATA_CACHE_KEY}_{sleeper_league_id}'
    league_data = cache.get(league_cache_key)
    if not league_data:
        league_data = fetch_and_cache_league_data(sleeper_league_id, league_cache_key)
    return league_data
