from datetime import datetime

from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework.decorators import api_view

from fantasy_trades_app.models import Players
from logger_util import logger
from sleeper_api.sleeper_api_svc import get_transactions, get_league, get_users, get_rosters

DRAFT_PICKS_JSON_FILE = 'sleeper_api/sleeper_data/draft_picks.json'


@api_view(['GET'])
def get_players_from_sleeper(request):
    None


@api_view(['GET'])
def get_players_from_sleeper_like(request, search_str):
    None


@api_view(['GET'])
def get_league_trades(request, sleeper_league_id):

    league_users = get_users(sleeper_league_id)
    league_rosters = get_rosters(sleeper_league_id)

    # Merge roster id with users and create a lookup dictionary
    league_users_dict = {
        user['user_id']: {
            'user_id': user['user_id'],
            'user_name': user['display_name'],
            'avatar_url': user['metadata'].get('avatar', None),
            'roster_id': next(
                (roster['roster_id'] for roster in league_rosters if roster['owner_id'] == user['user_id']),
                None
            )
        }
        for user in league_users
    }

    # Get previous_league_ids
    previous_leagues = []
    league_data = get_league(sleeper_league_id)
    temp_league_data = league_data
    while True:
        previous_league_id = temp_league_data['previous_league_id']
        if not previous_league_id:
            break

        temp_league_data = get_league(previous_league_id)
        previous_leagues.append(
            {
                'previous_league_id': previous_league_id,
                'season': temp_league_data['season']
            }
        )

    logger.info(f"Getting transactions from sleeper league: id={sleeper_league_id} name={league_data['name']}, league_history_count={len(previous_leagues)}")

    # Get trades from current league history
    all_trades = []
    for week in range(21):
        trade_response = get_transactions(sleeper_league_id, week)
        trade_response = [
            {
                'created_at_millis': item['created'],
                'created_at_formatted': datetime.fromtimestamp(item['created'] / 1000).strftime('%b %d %Y'),
                'draft_picks': item['draft_picks'],
                'adds': item['adds'],
                'consenter_ids': item['consenter_ids'],
                'drops': item['drops'],
                'roster_ids': item['roster_ids'],
                'transaction_id': item['transaction_id'],
                'week': item['leg']  # week
            }
            for item in trade_response
            if item.get('type') == 'trade'
               and item.get('status') == 'complete'
               and item.get('adds') is not None
        ]

        if not trade_response or len(trade_response) == 0:
            continue

        all_trades.extend(trade_response)

    logger.info(f"Found {len(all_trades)} trades")

    # Get all player IDs from the trades (adds and drops) in a single query
    player_ids = set()
    for trade in all_trades:
        player_ids.update(trade['adds'].keys())
        player_ids.update(trade['drops'].keys())

    # Fetch all players at once, using only the necessary fields
    players = Players.objects.filter(sleeper_player_id__in=player_ids).values('sleeper_player_id', 'player_name')
    player_dict = {player['sleeper_player_id']: player for player in players}

    updated_trades = []
    for trade in all_trades:
        # Handle 'adds' with a single player and user lookup
        updated_adds = []
        for key_player_id, value_roster_id in trade['adds'].items():
            player = player_dict.get(key_player_id, None)
            user = league_users_dict.get(value_roster_id, None)

            updated_adds.append({
                'player_id': key_player_id,
                'player_name': player['player_name'] if player else None,
                'roster_id': value_roster_id,
                'user_name': user['user_name'] if user else None,
                'avatar_url': user['avatar_url'] if user else None,
                'user_id': user['user_id'] if user else None,
            })

        # Handle 'drops' with a single player and user lookup
        updated_drops = []
        for key_player_id, value_roster_id in trade['drops'].items():
            player = player_dict.get(key_player_id, None)
            user = league_users_dict.get(value_roster_id, None)

            updated_drops.append({
                'player_id': key_player_id,
                'player_name': player['player_name'] if player else None,
                'roster_id': value_roster_id,
                'user_name': user['user_name'] if user else None,
                'avatar_url': user['avatar_url'] if user else None,
                'user_id': user['user_id'] if user else None,
            })

        trade['adds'] = updated_adds
        trade['drops'] = updated_drops
        updated_trades.append(trade)

    # Paginate the result
    page = request.GET.get('page', 1)
    logger.info(f"Getting league trades page: {page}")
    page_size = 20

    api_response = {
        'previous_league_ids': previous_leagues,
        'trades': updated_trades
    }

    # paginate the trades
    paginator = Paginator(api_response['trades'], page_size)

    try:
        paginated_trades = paginator.page(page)
    except PageNotAnInteger:
        paginated_trades = paginator.page(1)
    except EmptyPage:
        paginated_trades = paginator.page(paginator.num_pages)

    # Prepare the paginated response
    response = {
        'previous_league_ids': api_response['previous_league_ids'],  # Include previous league IDs
        'trades': list(paginated_trades.object_list),  # Paginated trades
        'page': paginated_trades.number,
        'total_pages': paginator.num_pages,
        'total_trades': paginator.count,
        'has_next': paginated_trades.has_next(),
        'has_previous': paginated_trades.has_previous(),
    }

    return JsonResponse(response, safe=False)
