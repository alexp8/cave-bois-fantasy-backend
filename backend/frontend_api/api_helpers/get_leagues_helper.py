from datetime import datetime

from sleeper_api.sleeper_api_svc import get_user_info, get_user_leagues

# get all the leagues that user is in
def get_leagues(username):

    # get user info
    user_info = get_user_info(username)

    # get user leagues
    user_leagues = get_user_leagues(user_info['user_id'], 'nfl', str(datetime.now().year))

    user_leagues: list = [
        {
            'league_id': user_league['league_id'],
            'name': user_league['name'],
            'avatar': user_league['avatar'],
            'season': user_league['season'],
            'sport': user_league['sport'],
            'type': get_league_type(user_league['settings']['type']),  # 0 = redraft, 1 = keeper, 2 = dynasty
        }
        for user_league in user_leagues
        if user_league['sport'] == 'nfl'
    ]

    return user_leagues

def get_league_type(league_type):
    return {
        0: 'Redraft',
        1: 'Keeper',
        2: 'Dynasty'
    }.get(league_type, 'Unknown')