from django.core.cache import cache
from frontend_api.cache.constants import CACHE_DURATION, LEAGUE_DRAFT_CACHE_KEY
from sleeper_api import sleeper_api_svc

def fetch_and_cache_draft_data(sleeper_league_id, cache_key):
    league_data = sleeper_api_svc.get_drafts(sleeper_league_id)
    if not league_data:
        raise Exception(f"No get_draft found for sleeper_league_id {sleeper_league_id}")
    cache.set(cache_key, league_data, timeout=CACHE_DURATION)
    return league_data


def get_data(sleeper_league_id):
    draft_cache_key = f'{LEAGUE_DRAFT_CACHE_KEY}_{sleeper_league_id}'
    draft_data = cache.get(draft_cache_key)
    if not draft_data:
        draft_data = fetch_and_cache_draft_data(sleeper_league_id, draft_cache_key)

    draft_data = draft_data[0]

    del draft_data['settings']
    del draft_data['season_type']
    del draft_data['start_time']
    del draft_data['type']
    del draft_data['status']
    del draft_data['metadata']
    del draft_data['last_message_id']
    del draft_data['last_message_time']
    del draft_data['last_picked']
    del draft_data['created']
    del draft_data['creators']
    del draft_data['sport']

    return draft_data
