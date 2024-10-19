import json
from datetime import datetime

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse

from fantasy_trades_app.models import Players, KtcPlayerValues
from frontend_api.cache.get_draft_data import get_draft_data
from frontend_api.cache.get_league_data import get_league_data
from frontend_api.cache.get_league_users import get_league_users_data
from frontend_api.cache.get_transactions_data import get_transactions_data
from logger_util import logger


def get_trades(request, sleeper_league_id, roster_id='all'):
    page = request.GET.get('page', 1)
    logger.info(f"Getting league trades for league: {sleeper_league_id}, roster_id: {roster_id}, page: {page}")

    # get sleeper league data
    league_data: json = get_league_data(sleeper_league_id)

    # fetch league_users
    league_users: list = get_league_users_data(sleeper_league_id)

    # Get previous_league_ids
    previous_leagues: list = get_previous_league_ids(league_data)

    # get draft data
    draft_response = get_draft_data(sleeper_league_id)[0]
    draft_order = {
        f"{draft_response['season']}_{key}": value
        for key, value in draft_response['draft_order'].items()
    }

    # get previous drafts data
    for previous_league in previous_leagues:
        draft_response = get_draft_data(previous_league['previous_league_id'])[0]
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

    # Get trades from current league
    all_trades: dict = get_transactions_data(sleeper_league_id)

    # Get trades from previous leagues history
    for previous_league in previous_leagues:
        all_trades.update(get_transactions_data(previous_league['previous_league_id']))

    # Get all player IDs from the trades (adds) in a single query
    player_ids = set()
    for sleeper_league_id, trades in all_trades.items():
        for trade in trades:
            if roster_id != 'all' and roster_id is int and int(roster_id) not in trade['roster_ids']:
                continue
            player_ids.update(trade['adds'].keys())

    # Fetch all players at once, using only the necessary fields
    players = Players.objects.filter(sleeper_player_id__in=player_ids).values('sleeper_player_id', 'player_name')
    player_dict = {player['sleeper_player_id']: player for player in players}

    # loop over trades and build response
    updated_trades = []
    for sleeper_league_id, trades in all_trades.items():
        for trade in trades:

            if roster_id != 'all' and roster_id is int and int(roster_id) not in trade['roster_ids']:
                continue

            trade_obj = {'sleeper_league_id': sleeper_league_id}

            # Initialize the roster_id entry in trade_obj
            for roster_id_temp in trade['roster_ids']:
                user = next((user for user in league_users if user['roster_id'] == roster_id_temp), None)
                trade_obj[roster_id_temp] = init_roster_trade(roster_id_temp, user)

            # get any fab
            for waiver_budget in trade['waiver_budget']:
                trade_obj[waiver_budget['receiver']]['fab'] += waiver_budget['amount']
                trade_obj[waiver_budget['sender']]['fab'] -= waiver_budget['amount']

            # grab values from draft picks
            for draft_pick in trade['draft_picks']:
                draft_pick_round = draft_pick['round']
                get_draft_pick_data(draft_order, draft_pick, draft_pick_round, league_users, trade_obj)

            # grab values from traded_players
            for key_player_id, value_roster_id in trade['adds'].items():
                result = get_traded_player_data(key_player_id, league_users, player_dict, sleeper_league_id, trade,
                                                trade_obj,
                                                value_roster_id)
                if not result:  # bad data found
                    continue

            trade_obj.update({
                'created_at_millis': trade['created_at_millis'],
                'created_at_pretty': trade['created_at_pretty'],
                'created_at_yyyy_mm_dd': trade['created_at_yyyy_mm_dd'],
                'transaction_id': trade['transaction_id'],
                'roster_ids': trade['roster_ids'],
                'week': trade['week']
            })

            # see who won the trade
            set_trade_winner(trade, trade_obj)

            updated_trades.append(trade_obj)

    # Sort the results most recent first
    updated_trades.sort(key=lambda trade: trade['created_at_millis'], reverse=True)

    # Paginate the result
    response = paginate_response(previous_leagues, page, updated_trades, league_data, league_users, roster_id)

    return JsonResponse(response, safe=False)


def get_traded_player_data(key_player_id, league_users, player_dict, sleeper_league_id, trade, trade_obj,
                           value_roster_id):
    player = player_dict.get(int(key_player_id))
    user = next((user for user in league_users if user['roster_id'] == value_roster_id), None)

    ktc_values = []

    if user is None:
        logger.warn(
            f"Failed to find user with roster_id {value_roster_id}, league={sleeper_league_id} for trade {trade}")
        return False
    if player is None:
        player = {"player_name": "Unknown Player"}
    else:

        # get ktc values
        ktc_values = (KtcPlayerValues.objects.filter(ktc_player_id__sleeper_player_id=key_player_id)
                      .filter(date__gte=trade['created_at_yyyy_mm_dd'])
                      .values('ktc_value', 'date')
                      .order_by('-date'))

        ktc_values = [
            {**item, 'date': item['date'].strftime("%Y-%m-%d")}
            for item in ktc_values
        ]

    # KTC value when traded
    value_when_traded = ktc_values[0]['ktc_value'] if ktc_values and len(ktc_values) > 0 else 0

    # latest KTC value
    latest_value = ktc_values[-1]['ktc_value'] if ktc_values and len(ktc_values) > 0 else 0
    latest_value_as_of = ktc_values[-1]['date'] if ktc_values and len(ktc_values) > 0 else 0

    trade_obj[value_roster_id]['players'].append({
        'player_id': key_player_id,
        'player_name': player['player_name'],
        'value_when_traded': value_when_traded,
        'ktc_values': ktc_values,
        'latest_value': latest_value,
        'value_now_as_of': latest_value_as_of
    })

    trade_obj[value_roster_id]['total_current_value'] += latest_value
    trade_obj[value_roster_id]['total_value_when_traded'] += value_when_traded
    return True


def get_draft_pick_data(draft_order, draft_pick, draft_pick_round, league_users, trade_obj):
    # get the user's draft position
    user = next((user for user in league_users if user['roster_id'] == draft_pick['owner_id']), None)
    key_order_key = f"{draft_pick['season']}_{user['user_id']}"
    draft_order_number = draft_order[key_order_key] if key_order_key in draft_order else None
    draft_pick_range = get_draft_pick_range(draft_order_number)
    draft_pick_value = 750  # 5th rd pick value

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
        'description': f"{draft_pick['season']} {draft_pick_range} {number_with_suffix(draft_pick['round'])} round",
        'latest_value': draft_pick_value,  # TODO get latest value for this draft pick
        'value_now_as_of': None  # TODO
    })

    trade_obj[draft_pick['owner_id']]['total_current_value'] += draft_pick_value
    trade_obj[draft_pick['owner_id']]['total_value_when_traded'] += draft_pick_value


def init_roster_trade(roster_id, user):
    return {
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


def set_trade_winner(trade, trade_obj):
    # Find the maximum total current value
    max_value = max(trade_obj[roster_id]['total_current_value'] for roster_id in trade['roster_ids'])

    # Mark the rosters with the maximum value as winners
    for roster_id in trade['roster_ids']:
        trade_obj[roster_id]['won'] = (trade_obj[roster_id]['total_current_value'] == max_value)


def paginate_response(previous_leagues, page, updated_trades, league_data, league_users, roster_id):
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
        'league_id': league_data['league_id'],
        'league_name': league_data['name'],
        'league_season': league_data['season'],
        'league_avatar': league_data['avatar'],
        'roster_id': roster_id,
        'page': paginated_trades.number,
        'page_size': page_size,
        'total_pages': paginator.num_pages,
        'total_trades': paginator.count,
        'has_next': paginated_trades.has_next(),
        'has_previous': paginated_trades.has_previous(),
        'previous_leagues': api_response['previous_league_ids'],  # Include previous league IDs
        'league_users': league_users,
        'trades': list(paginated_trades.object_list)  # Paginated trades
    }


def get_previous_league_ids(league_data):
    previous_leagues: list = []

    while True:
        previous_league_id = league_data['previous_league_id']
        if not previous_league_id or previous_league_id == "0":
            break

        league_data: json = get_league_data(previous_league_id)
        previous_leagues.append(
            {
                'previous_league_id': previous_league_id,
                'season': league_data['season']
            }
        )
    return previous_leagues


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


def number_with_suffix(val):
    val = int(val)
    if val == 1:
        return "1st"
    elif val == 2:
        return "2nd"
    elif val == 3:
        return "3rd"
    elif val == 4:
        return "4th"
    elif val == 5:
        return "5th"
    else:
        return ""
