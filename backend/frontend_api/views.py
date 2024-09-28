import logging

from django.http import JsonResponse
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from rest_framework.decorators import api_view

from fantasy_trades_app.models import Players
from sleeper_api.sleeper_api_svc import get_players, get_transactions, get_league

DRAFT_PICKS_JSON_FILE = 'sleeper_api/sleeper_data/draft_picks.json'

# Use the logger from the global settings
logger = logging.getLogger('django')


@api_view(['GET'])
def get_players_from_sleeper(request):
    None


@api_view(['GET'])
def get_players_from_sleeper_like(request, search_str):
    None


@api_view(['GET'])
def get_league_trades(request, sleeper_league_id):
    all_transactions = []
    all_league_ids = [sleeper_league_id]

    # get previous_league_ids
    previous_league_id = None
    while True:
        if previous_league_id:
            league_data = get_league(previous_league_id)
        else:
            league_data = get_league(sleeper_league_id)

        previous_league_id = league_data['previous_league_id']
        if not previous_league_id:
            break
        all_league_ids.append(previous_league_id)

    logger.info(f"Getting transactions from leagues {all_league_ids}")

    # get trades from entire league history
    for league_id in all_league_ids:
        for week in range(21):
            transactions_data = get_transactions(league_id, week)
            transactions_data = [
                {
                    'created': item['created'],
                    'draft_picks': item['draft_picks'],
                    'adds': item['adds'],
                    'consenter_ids': item['consenter_ids'],
                    'drops': item['drops'],
                    'roster_ids': item['roster_ids'],
                    'transaction_id': item['transaction_id']
                }
                for item in transactions_data
                if item.get('type') == 'trade' and item.get('status') == 'complete'
            ]

            if not transactions_data or len(transactions_data) == 0:
                continue

            all_transactions.extend(transactions_data)

    # populate additional information needed, i.e. player_names and user_names
    updated_transactions = []
    for transaction in all_transactions:
        updated_adds = []
        for key, value in transaction['adds'].items():
            player = Players.objects.get(sleeper_player_id=key)
            updated_adds.append({
                'player_id': key,
                'player_name': player.player_name,
                'user_id': value,
                'user_name': None  # TODO find username
            })

        transaction['adds'] = updated_adds
        updated_transactions.append(transaction)

    # Paginate the result
    page = request.GET.get('page', 1)
    page_size = 20

    paginator = Paginator(updated_transactions, page_size)

    try:
        paginated_transactions = paginator.page(page)
    except PageNotAnInteger:
        paginated_transactions = paginator.page(1)
    except EmptyPage:
        paginated_transactions = paginator.page(paginator.num_pages)

    # Prepare paginated response
    response = {
        'transactions': list(paginated_transactions.object_list),
        'page': paginated_transactions.number,
        'total_pages': paginator.num_pages,
        'total_transactions': paginator.count,
        'has_next': paginated_transactions.has_next(),
        'has_previous': paginated_transactions.has_previous(),
    }

    return JsonResponse(response, safe=False)
