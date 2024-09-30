from datetime import datetime

from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework.decorators import api_view

from fantasy_trades_app.models import Players, KtcPlayerValues
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
    league_users = [
        {
            'user_id': user['user_id'],
            'user_name': user['display_name'],
            'avatar_url': user['metadata'].get('avatar', None),
            'roster_id': next(
                (roster['roster_id'] for roster in league_rosters if roster['owner_id'] == user['user_id']),
                None
            )
        }
        for user in league_users
    ]

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

    logger.info(
        f"Getting transactions from sleeper league: id={sleeper_league_id} name={league_data['name']}, league_history_count={len(previous_leagues)}")

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
                # 'consenter_ids': item['consenter_ids'],
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

    # Get all player IDs from the trades (adds) in a single query
    player_ids = set()
    for trade in all_trades:
        player_ids.update(trade['adds'].keys())

    # Fetch all players at once, using only the necessary fields
    players = Players.objects.filter(sleeper_player_id__in=player_ids).values('sleeper_player_id', 'player_name')
    player_dict = {player['sleeper_player_id']: player for player in players}
    logger.info(f'player_ids: {player_dict.keys()}')

    updated_trades = []
    for trade in all_trades:

        trade_obj = {}
        for key_player_id, value_roster_id in trade['adds'].items():
            player = player_dict.get(int(key_player_id))
            user = next((user for user in league_users if user['roster_id'] == value_roster_id), None)

            if user is None:
                raise Exception(f'Failed to find user with roster_id {value_roster_id}')

            if player is None:
                raise Exception(f"Failed to find player with player_id '{key_player_id}'")

            # Initialize the roster_id entry in trade_obj if it doesn't exist
            if value_roster_id not in trade_obj:
                trade_obj[value_roster_id] = {
                    'total_value': 0,  # TODO logic to calculate this
                    'user_name': user['user_name'],
                    'avatar_url': user['avatar_url'],
                    'user_id': user['user_id'],
                    'roster_id': value_roster_id,
                    'players': []
                }

            # Add player details to the 'players' list
            trade_obj[value_roster_id]['players'].append({
                'player_id': key_player_id,
                'player_name': player['player_name'],
                'value_when_traded': None, #TODO
                'value_now': None # TODO
                # 'value_when_traded': KtcPlayerValues.objects.filter(
                #     ktc_player_id__sleeper_player_id=player['sleeper_player_id'],
                #     date=datetime.fromtimestamp(trade['created'] / 1000).strftime('%Y-%m-%d')
                # ).first(),
                # 'value_now': KtcPlayerValues.objects.filter(
                #     ktc_player_id__sleeper_player_id=player['sleeper_player_id'],
                #     date=datetime.now().strftime('%Y-%m-%d')
                # ).first()
            })

            # Logic to calculate the 'total_value' per roster (e.g., based on KTC values)
            # trade_obj[value_roster_id]['total_value'] += calculate_player_value(key_player_id)
            trade_obj[value_roster_id]['total_value'] += 0

            # Add the trade metadata
        trade_obj.update({
            'created_at_millis': trade['created_at_millis'],
            'created_at_formatted': trade['created_at_formatted'],
            'transaction_id': trade['transaction_id'],
            'roster_ids': trade['roster_ids'],
            'week': trade['week']
        })

        updated_trades.append(trade_obj)

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


def calculate_player_value(player_id):
    # Example logic to get a player's trade value
    ktc_value = KtcPlayerValues.objects.filter(
        ktc_player_id__sleeper_player_id=player_id,
        date="2023-01-01"  # Example date, adjust as necessary
    ).first()
    return ktc_value.ktc_value if ktc_value else 0
