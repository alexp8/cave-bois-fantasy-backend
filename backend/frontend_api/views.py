import logging

from django.http import JsonResponse
from rest_framework.decorators import api_view
from sleeper_api.sleeper_api_svc import get_players, get_transactions, get_league
import json
import os

from util import load_json

DRAFT_PICKS_JSON_FILE = 'sleeper_api/sleeper_data/draft_picks.json'

# Use the logger from the global settings
logger = logging.getLogger('django')

@api_view(['GET'])
def get_players_from_sleeper(request):
   None




@api_view(['GET'])
def get_players_from_sleeper_like(request, search_str):
    None

    # TODO a smart filter that puts most 'relevant' players on top

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
        for i in range(21):

            # store previous years trade data, to prevent unnecessary API calls
            transactions_data = None
            file_path = f'sleeper_data/{league_id}_league_data.json'
            if league_id != sleeper_league_id and os.path.exists(file_path):
                transactions_data = load_json(file_path)
            else:
                transactions_data = get_transactions(league_id, i)
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

                # store transaction json data of previous years
                if league_id != sleeper_league_id:
                    with open(file_path, 'w') as json_file:
                        logger.info(f"Writing transaction data to {file_path}")
                        json.dump(transactions_data, json_file, indent=4) # TODO store in DB?

            all_transactions.extend(transactions_data)

    return JsonResponse(all_transactions, safe=False)
