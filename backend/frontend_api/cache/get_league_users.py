import json

from django.core.cache import cache

from frontend_api.cache.constants import CACHE_DURATION, LEAGUE_USERS_CACHE_KEY
from frontend_api.models import LeagueUser
from sleeper_api import sleeper_api_svc


def get_data(sleeper_league_id) -> list[LeagueUser]:
    cache_key = f"{LEAGUE_USERS_CACHE_KEY}_{sleeper_league_id}"
    league_users_data = cache.get(cache_key)

    if not league_users_data:
        league_users_data = fetch_league_users(sleeper_league_id)
        cache.set(cache_key, league_users_data, timeout=CACHE_DURATION)

        if not league_users_data:
            raise Exception(f"No league users data found for sleeper_league_id {sleeper_league_id}")

    league_users: list = [LeagueUser.from_json(league_user) for league_user in league_users_data]

    return league_users


def fetch_league_users(sleeper_league_id) -> list[json]:
    league_users_json: json = sleeper_api_svc.get_users(sleeper_league_id)
    league_rosters_json: json = sleeper_api_svc.get_rosters(sleeper_league_id)

    return [
        {
            'user_id': league_user['user_id'],
            'user_name': league_user['display_name'],
            'roster_avatar': league_user['metadata'].get('avatar', None),
            'user_avatar': league_user['avatar'],
            'roster_id': next(
                (roster['roster_id'] for roster in league_rosters_json if roster['owner_id'] == league_user['user_id']),
                None
            )
        }
        for league_user in league_users_json
    ]
