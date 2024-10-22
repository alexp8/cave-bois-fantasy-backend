import json
from datetime import datetime

from sleeper_api import sleeper_api_svc


# get all the leagues that user is in
def get_leagues(username: str) -> list[json]:
    # get user info
    user_info: json = sleeper_api_svc.get_user_info(username=username)

    # get user leagues
    user_leagues: json = sleeper_api_svc.get_user_leagues(
        user_id=user_info['user_id'],
        sport='nfl',
        season=str(datetime.now().year)
    )

    user_leagues: list[json] = [
        {
            'league_id': user_league['league_id'],
            'name': user_league['name'],
            'avatar': user_league['avatar'],
            'season': user_league['season'],
            'sport': user_league['sport'],
            'type_index': user_league['settings']['type'],
            'type': get_league_type(user_league['settings']['type']),  # 0 = redraft, 1 = keeper, 2 = dynasty
        }
        for user_league in user_leagues
        if user_league['sport'] == 'nfl'
    ]

    user_leagues.sort(key=lambda user_l: user_l['type_index'], reverse=True)

    return user_leagues


def get_league_type(league_type: int) -> str:
    return {
        0: 'Redraft',
        1: 'Keeper',
        2: 'Dynasty'
    }.get(league_type, 'Unknown')
