import json
from collections import defaultdict
from datetime import datetime

from django.core.paginator import Paginator

from fantasy_trades_app.models import Players, KtcPlayerValues
from frontend_api.cache import get_drafts_data, get_draft_picks_data
from frontend_api.cache.get_league_data import get_league_data
from frontend_api.cache.get_league_users import get_league_users_data
from frontend_api.cache.get_transactions_data import get_transactions_data
from logger_util import logger

PAGE_SIZE = 20


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
    draft_picks_dict = get_draft_data(sleeper_league_id, previous_leagues)

    logger.info(
        f"Getting transactions from sleeper league: "
        f"id={sleeper_league_id} "
        f"name={league_data['name']},"
        f" league_history_count={len(previous_leagues)}"
    )

    # Get trades from current league
    all_trades: list = get_transactions_data(sleeper_league_id)

    # Get trades from previous leagues history
    for previous_league in previous_leagues:
        all_trades.extend(get_transactions_data(previous_league['previous_league_id']))

    # filter out trades belonging to different roster_ids
    if roster_id != 'all':
        all_trades = [trade for trade in all_trades if int(roster_id) in trade['roster_ids']]

    # apply pagination
    paginator = Paginator(all_trades, PAGE_SIZE)
    paginated_trades = paginator.get_page(page)

    # Get all player IDs from the trades (adds) in a single query
    player_ids = set()
    for trade in paginated_trades:
        if roster_id != 'all' and roster_id is int and int(roster_id) not in trade['roster_ids']:
            continue
        player_ids.update(trade['adds'].keys())

    # Fetch all players at once, using only the necessary fields
    players = Players.objects.filter(sleeper_player_id__in=player_ids).values('sleeper_player_id', 'player_name')
    player_dict = {player['sleeper_player_id']: player for player in players}

    # loop over trades and build response
    updated_trades = calculate_trade_values(draft_picks_dict, league_users, paginated_trades, player_dict, roster_id)

    # build response
    return {
        'league_id': league_data['league_id'],
        'league_name': league_data['name'],
        'league_season': league_data['season'],
        'league_avatar': league_data['avatar'],
        'roster_id': roster_id,
        'page': paginated_trades.number,
        'page_size': PAGE_SIZE,
        'total_pages': paginator.num_pages,
        'total_trades': paginator.count,
        'has_next': paginated_trades.has_next(),
        'has_previous': paginated_trades.has_previous(),
        'previous_leagues': previous_leagues,
        'league_users': league_users,
        'trades': updated_trades
    }


def get_draft_data(sleeper_league_id, previous_leagues):
    draft_data_dict = {}
    all_drafts = []
    draft_data = get_drafts_data.get_data(sleeper_league_id)[0]
    all_drafts.append(draft_data)

    # get previous drafts data
    for previous_league in previous_leagues:
        draft_response = get_drafts_data.get_data(previous_league['previous_league_id'])[0]
        all_drafts.append(draft_response)

    for draft in all_drafts:
        draft_picks = get_draft_picks_data.get_data(draft['draft_id'])
        draft_data_dict[draft['season']] = draft_picks

    return draft_data_dict


# Iterate over a list of trades and calculate values
def calculate_trade_values(draft_picks_dict, league_users, paginated_trades, player_dict, roster_id):
    updated_trades = []

    for trade in paginated_trades:

        if roster_id != 'all' and roster_id is int and int(roster_id) not in trade['roster_ids']:
            continue

        trade_obj = {'sleeper_league_id': trade['sleeper_league_id']}

        # Initialize the roster_id entry in trade_obj
        for roster_id_temp in trade['roster_ids']:
            user = next((user for user in league_users if user['roster_id'] == roster_id_temp), None)
            trade_obj[roster_id_temp] = init_roster_trade(roster_id_temp, user)

        # get any fab
        for waiver_budget in trade['waiver_budget']:
            trade_obj[waiver_budget['receiver']]['fab'] += waiver_budget['amount']
            trade_obj[waiver_budget['sender']]['fab'] -= waiver_budget['amount']

        # grab values from draft picks
        for traded_draft_pick in trade['draft_picks']:
            draft_pick_round = traded_draft_pick['round']
            get_draft_pick_data(draft_picks_dict, traded_draft_pick, league_users, trade_obj)

        # grab values from traded_players
        for key_player_id, value_roster_id in trade['adds'].items():
            get_traded_player_data(key_player_id, player_dict, trade, trade_obj, value_roster_id)

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

    updated_trades.sort(key=lambda trade_t: trade_t['created_at_millis'], reverse=True)

    return updated_trades


# reduce values returned, grab one value per week
def trim_ktc_values(ktc_values):
    # convert dates from string to date
    for ktc_value in ktc_values:
        ktc_value['date'] = datetime.strptime(ktc_value['date'], '%Y-%m-%d')
    data = sorted(ktc_values, key=lambda x: x['date'])

    # Group entries by year-month
    grouped_by_month = defaultdict(list)
    for entry in data:
        year_month = entry['date'].strftime('%Y-%m')
        grouped_by_month[year_month].append(entry)

    # Select one entry per week per month
    trimmed_data = []
    for year_month, entries in grouped_by_month.items():
        weeks = defaultdict(list)
        for entry in entries:
            week = entry['date'].strftime('%U')
            weeks[week].append(entry)

        # Select one entry per week
        for week_entries in weeks.values():
            trimmed_data.append(week_entries[0])

    # Convert datetime objects back to date strings
    for entry in trimmed_data:
        entry['date'] = entry['date'].strftime('%Y-%m-%d')

    return trimmed_data
    # Optionally, sort the final trimmed data by date
    # return sorted(trimmed_data, key=lambda x: x['date'])


def get_traded_player_data(key_player_id, player_dict, trade, trade_obj,
                           value_roster_id):
    player = player_dict.get(int(key_player_id))

    ktc_values = []

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

        # reduce values returned
        ktc_values = trim_ktc_values(ktc_values)

    # KTC value when traded
    value_when_traded = ktc_values[0]['ktc_value'] if ktc_values and len(ktc_values) > 0 else 0

    # latest KTC value
    latest_value = ktc_values[-1]['ktc_value'] if ktc_values and len(ktc_values) > 0 else 0
    latest_value_as_of = ktc_values[-1]['date'] if ktc_values and len(ktc_values) > 0 else ''

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


def get_draft_pick_data(draft_picks_dict, traded_draft_pick, trade_obj):

    # the draft pick was used to select a player
    if traded_draft_pick['season'] in draft_picks_dict:

        # TODO get the player that was drafted with the draft pick
        draft = draft_picks_dict[traded_draft_pick['season']]
        draft_pick_player = next((draft_pick for draft_pick in draft if draft_pick['roster_id'] == traded_draft_pick['roster_id']), None)
        if draft_pick_player is None:
            raise Exception(f"Unable to find draft pick for roster_id {traded_draft_pick['roster_id']} in draft {draft}")

        player_id_drafted = draft_pick_player['player_id']
        # TODO get ktc value of this player

    # Draft pick is a future pick
    else:

        if traded_draft_pick['round'] < 5: # rounds 1-4 have KTC values
            draft_filter = f"{traded_draft_pick['season']} Mid {traded_draft_pick['round']}"
            draft_pick_player = Players.objects.filter(player_name__icontains=draft_filter).first()

            if draft_pick_player is None:
                raise Exception(f"Unable to find draft pick '{draft_filter}'")

            # get the draft pick's value
            draft_pick_player_value = KtcPlayerValues.objects.filter(
                ktc_player_id=draft_pick_player.ktc_player_id).first()

            if draft_pick_player:
                draft_pick_value = draft_pick_player_value.ktc_value

    trade_obj[traded_draft_pick['owner_id']]['draft_picks'].append({
        'round': traded_draft_pick['round'],
        'season': traded_draft_pick['season'],
        'value_when_traded': draft_pick_value,
        'description': f"{traded_draft_pick['season']} {number_with_suffix(traded_draft_pick['round'])} round",
        'latest_value': draft_pick_value,
        'value_now_as_of': None  # TODO
    })

    trade_obj[traded_draft_pick['owner_id']]['total_current_value'] += draft_pick_value
    trade_obj[traded_draft_pick['owner_id']]['total_value_when_traded'] += draft_pick_value


def init_roster_trade(roster_id, user):
    return {
        'total_current_value': 0,
        'total_value_when_traded': 0,
        'user_name': user['user_name'],
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
