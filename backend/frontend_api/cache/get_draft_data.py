from django.core.cache import cache
from frontend_api.cache.constants import CACHE_DURATION, LEAGUE_DRAFT_CACHE_KEY
from sleeper_api.sleeper_api_svc import get_draft

def fetch_and_cache_draft_data(sleeper_league_id, cache_key):
    league_data = get_draft(sleeper_league_id)
    if not league_data:
        raise Exception(f"No get_draft found for sleeper_league_id {sleeper_league_id}")
    cache.set(cache_key, league_data, timeout=CACHE_DURATION)
    return league_data


def get_draft_data(sleeper_league_id):
    draft_cache_key = f'{LEAGUE_DRAFT_CACHE_KEY}_{sleeper_league_id}'
    draft_data = cache.get(draft_cache_key)
    if not draft_data:
        draft_data = fetch_and_cache_draft_data(sleeper_league_id, draft_cache_key)
    return draft_data
