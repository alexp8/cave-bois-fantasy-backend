from datetime import datetime

from django.core.cache import cache

from frontend_api.cache.constants import LEAGUE_TRANSACTIONS_CACHE_KEY, CACHE_DURATION
from logger_util import logger
from sleeper_api.sleeper_api_svc import get_transactions

NUMBER_OF_WEEKS = 21


def transform_transaction_data(item):
    return {
        'created_at_millis': item['status_updated'],
        'created_at_yyyy_mm_dd': datetime.fromtimestamp(item['status_updated'] / 1000).strftime('%Y-%m-%d'),
        'created_at_pretty': datetime.fromtimestamp(item['status_updated'] / 1000).strftime('%b %d %Y'),
        'draft_picks': item['draft_picks'],
        'adds': item['adds'],
        'roster_ids': item['roster_ids'],
        'transaction_id': item['transaction_id'],
        'waiver_budget': item['waiver_budget'],
        'week': item['leg']
    }


def get_transactions_data(sleeper_league_id):
    all_trades = {}
    trades_list = []

    for week in range(NUMBER_OF_WEEKS):
        cache_key = f"{LEAGUE_TRANSACTIONS_CACHE_KEY}_{sleeper_league_id}_{week}"
        league_transactions_data = cache.get(cache_key)

        if not league_transactions_data:
            league_transactions_data = get_transactions(sleeper_league_id, week)  # query sleeper API
            league_transactions_data = [
                transform_transaction_data(item)
                for item in league_transactions_data
                if item.get('type') == 'trade'
                   and item.get('status') == 'complete'
                   and item.get('adds') is not None
            ]
            cache.set(cache_key, league_transactions_data, timeout=CACHE_DURATION)

        if not league_transactions_data:
            continue
        trades_list.extend(league_transactions_data)

    if trades_list:
        all_trades[sleeper_league_id] = trades_list
    logger.info(f"Found {len(trades_list)} trades for league ID {sleeper_league_id}")
    return all_trades
