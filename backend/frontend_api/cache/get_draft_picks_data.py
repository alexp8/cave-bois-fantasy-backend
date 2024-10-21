from django.core.cache import cache

from frontend_api.cache.constants import CACHE_DURATION, LEAGUE_DRAFT_PICKS_CACHE_KEY
from sleeper_api import sleeper_api_svc


def fetch_and_cache_draft_picks_data(draft_id, cache_key):
    draft_picks_data = sleeper_api_svc.get_draft_picks(draft_id)
    if not draft_picks_data:
        raise Exception(f"No draft picks data found for sleeper_league_id {draft_id}")
    cache.set(cache_key, draft_picks_data, timeout=CACHE_DURATION)
    return draft_picks_data


def get_data(draft_id):
    draft_cache_key = f'{LEAGUE_DRAFT_PICKS_CACHE_KEY}_{draft_id}'
    draft_data = cache.get(draft_cache_key)
    if not draft_data:
        draft_data = fetch_and_cache_draft_picks_data(draft_id, draft_cache_key)
    return draft_data
