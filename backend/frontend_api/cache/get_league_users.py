import json

from django.core.cache import cache
from frontend_api.cache.constants import CACHE_DURATION, LEAGUE_USERS_CACHE_KEY
from sleeper_api import sleeper_api_svc

def get_league_users_data(sleeper_league_id):

    cache_key = f"{LEAGUE_USERS_CACHE_KEY}_{sleeper_league_id}"
    league_users_data = cache.get(cache_key)

    if not league_users_data:
        league_users_data = fetch_league_users(sleeper_league_id)
        cache.set(cache_key, league_users_data, timeout=CACHE_DURATION)

        if not league_users_data:
            raise Exception(f"No league users data found for sleeper_league_id {sleeper_league_id}")

    return league_users_data

def fetch_league_users(sleeper_league_id):
    league_users: json = sleeper_api_svc.get_users(sleeper_league_id)
    league_rosters: json = sleeper_api_svc.get_rosters(sleeper_league_id)

    league_users: list = [
        {
            'user_id': user['user_id'],
            'user_name': user['display_name'],
            'roster_avatar': user['metadata'].get('avatar', None),
            'user_avatar': user['avatar'],
            'roster_id': next(
                (roster['roster_id'] for roster in league_rosters if roster['owner_id'] == user['user_id']),
                None
            )
        }
        for user in league_users
    ]
    return league_users