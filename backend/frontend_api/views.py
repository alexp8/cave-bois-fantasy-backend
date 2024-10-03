import json
from datetime import datetime

from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework.decorators import api_view

from fantasy_trades_app.models import Players, KtcPlayerValues
from logger_util import logger
from sleeper_api.sleeper_api_svc import get_transactions, get_league, get_users, get_rosters, get_draft


@api_view(['GET'])
def get_players_from_sleeper(request):
    None


@api_view(['GET'])
def get_players_from_sleeper_like(request, search_str):
    None


def get_draft_pick_range(draft_order_number):
    if draft_order_number is None:
        return 'Mid'
    elif draft_order_number <= 4:  # 1-4
        return 'Early'
    elif draft_order_number <= 8:  # 5-8
        return 'Mid'
    elif draft_order_number > 8:  # 9-12
        return 'Late'
    else:
        return 'Unknown'


@api_view(['GET'])
def get_league_trades(request, sleeper_league_id):

    # get sleeper league data
    league_data: json = get_league(sleeper_league_id)

    if not league_data:
        raise Exception(f"No data found for sleeper_league_id {sleeper_league_id}")

    # fetch league_users
    league_users: list = fetch_league_users(sleeper_league_id)

    # Get previous_league_ids
    previous_leagues: list = get_previous_league_ids(league_data)

    # get draft data
    draft_response = get_draft(sleeper_league_id)[0]
    draft_order = {
        f"{draft_response['season']}_{key}": value
        for key, value in draft_response['draft_order'].items()
    }

    # get previous drafts data
    for previous_league in previous_leagues:
        draft_response = get_draft(previous_league['previous_league_id'])[0]
        draft_order.update({
            f"{draft_response['season']}_{key}": value
            for key, value in draft_response['draft_order'].items()
        })

    logger.info(
        f"Getting transactions from sleeper league: "
        f"id={sleeper_league_id} "
        f"name={league_data['name']},"
        f" league_history_count={len(previous_leagues)}"
    )

    # Get trades from current league history
    all_trades: list = fetch_trade_data(sleeper_league_id)

    # Get all player IDs from the trades (adds) in a single query
    player_ids = set()
    for trade in all_trades:
        player_ids.update(trade['adds'].keys())

    # Fetch all players at once, using only the necessary fields
    players = Players.objects.filter(sleeper_player_id__in=player_ids).values('sleeper_player_id', 'player_name')
    player_dict = {player['sleeper_player_id']: player for player in players}
    logger.info(f'player_ids: {player_dict.keys()}')

    # loop over trades and build response
    updated_trades = []
    for trade in all_trades:

        trade_obj = {}

        # Initialize the roster_id entry in trade_obj
        for roster_id in trade['roster_ids']:
            user = next((user for user in league_users if user['roster_id'] == roster_id), None)
            trade_obj[roster_id] = {
                'total_current_value': 0,
                'total_value_when_traded': 0,
                'user_name': user['user_name'],
                'avatar_url': user['avatar_url'],
                'user_id': user['user_id'],
                'roster_id': roster_id,
                'fab': 0,
                'players': [],
                'draft_picks': []
            }

        # get any fab
        for waiver_budget in trade['waiver_budget']:
            trade_obj[waiver_budget['receiver']]['fab'] += waiver_budget['amount']
            trade_obj[waiver_budget['sender']]['fab'] -= waiver_budget['amount']

        # grab values from draft picks
        for draft_pick in trade['draft_picks']:
            draft_pick_round = draft_pick['round']

            # get the user's draft position
            user = next((user for user in league_users if user['roster_id'] == draft_pick['owner_id']), None)
            key_order_key = f"{draft_pick['season']}_{user['user_id']}"
            draft_order_number = draft_order[key_order_key] if key_order_key in draft_order else None
            draft_pick_range = get_draft_pick_range(draft_order_number)
            logger.info(f"{draft_pick['season']}_{user['user_id']} - {draft_order_number}")

            draft_pick_value = 750
            if draft_pick_round < 5:
                draft_filter = f"{draft_pick_range} {draft_pick_round}"
                draft_pick_player = Players.objects.filter(player_name__icontains=draft_filter).first()

                if draft_pick_player is None:
                    raise Exception(f"Unable to find draft pick '{draft_filter}'")

                # get the draft pick's value
                draft_pick_player_value = KtcPlayerValues.objects.filter(
                    ktc_player_id=draft_pick_player.ktc_player_id).first()

                if draft_pick_player:
                    draft_pick_value = draft_pick_player_value.ktc_value

            trade_obj[draft_pick['owner_id']]['draft_picks'].append({
                'round': draft_pick['round'],
                'range': draft_pick_range,
                'season': draft_pick['season'],
                'value_when_traded': draft_pick_value,
                'latest_value': draft_pick_value,  # TODO get latest value for this draft pick
                'value_now_as_of': None  # TODO
            })
            trade_obj[draft_pick['owner_id']]['total_current_value'] += draft_pick_value
            trade_obj[draft_pick['owner_id']]['total_value_when_traded'] += draft_pick_value

        # grab values from traded_players
        for key_player_id, value_roster_id in trade['adds'].items():
            player = player_dict.get(int(key_player_id))
            user = next((user for user in league_users if user['roster_id'] == value_roster_id), None)

            if user is None:
                raise Exception(f'Failed to find user with roster_id {value_roster_id}')

            if player is None:
                raise Exception(f"Failed to find player with player_id '{key_player_id}'")

            # ktc latest value
            ktc_value_latest = (KtcPlayerValues.objects.filter(ktc_player_id__sleeper_player_id=key_player_id)
                                .order_by('-date').first())

            # ktc value when traded
            date_when_traded = datetime.fromtimestamp(trade['created_at_millis'] / 1000).strftime('%Y-%m-%d')
            ktc_value_when_traded = KtcPlayerValues.objects.filter(ktc_player_id__sleeper_player_id=key_player_id,
                                                                   date=date_when_traded).first()

            trade_obj[value_roster_id]['players'].append({
                'player_id': key_player_id,
                'player_name': player['player_name'],
                'value_when_traded': ktc_value_when_traded.ktc_value if ktc_value_when_traded else None,
                'latest_value': ktc_value_latest.ktc_value if ktc_value_latest else None,
                'value_now_as_of': ktc_value_latest.date if ktc_value_latest else None,
            })

            trade_obj[value_roster_id]['total_current_value'] += ktc_value_latest.ktc_value if ktc_value_latest else 0
            trade_obj[value_roster_id][
                'total_value_when_traded'] += ktc_value_when_traded.ktc_value if ktc_value_when_traded else 0

        trade_obj.update({
            'created_at_millis': trade['created_at_millis'],
            'created_at_formatted': trade['created_at_formatted'],
            'transaction_id': trade['transaction_id'],
            'roster_ids': trade['roster_ids'],
            'week': trade['week']
        })

        updated_trades.append(trade_obj)

    # Paginate the result
    response = paginate_response(previous_leagues, request, updated_trades)

    return JsonResponse(response, safe=False)


def paginate_response(previous_leagues, request, updated_trades):
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
    return {
        'page': paginated_trades.number,
        'total_pages': paginator.num_pages,
        'total_trades': paginator.count,
        'has_next': paginated_trades.has_next(),
        'has_previous': paginated_trades.has_previous(),
        'previous_league_ids': api_response['previous_league_ids'],  # Include previous league IDs
        'trades': list(paginated_trades.object_list)  # Paginated trades
    }


def fetch_trade_data(sleeper_league_id):
    all_trades: list = []
    for week in range(21):

        # fetch trades from sleeper
        trade_response: json = get_transactions(sleeper_league_id, week)
        trade_response = [
            {
                'created_at_millis': item['created'],
                'created_at_formatted': datetime.fromtimestamp(item['created'] / 1000).strftime('%b %d %Y'),
                'draft_picks': item['draft_picks'],
                'adds': item['adds'],
                'roster_ids': item['roster_ids'],
                'transaction_id': item['transaction_id'],
                'waiver_budget': item['waiver_budget'],
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
    return all_trades


def get_previous_league_ids(league_data):
    previous_leagues: list = []
    temp_league_data: json = league_data
    while True:
        previous_league_id = temp_league_data['previous_league_id']
        if not previous_league_id:
            break

        temp_league_data: json = get_league(previous_league_id)
        previous_leagues.append(
            {
                'previous_league_id': previous_league_id,
                'season': temp_league_data['season']
            }
        )
    return previous_leagues


def fetch_league_users(sleeper_league_id):

    league_users: json = get_users(sleeper_league_id)
    league_rosters: json = get_rosters(sleeper_league_id)

    # Merge roster id with users and create a lookup dictionary
    league_users: list = [
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
    return league_users
