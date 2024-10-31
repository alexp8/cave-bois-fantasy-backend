import json

from requests import Request
from typing import List, Dict, Any
from frontend_api.api_helpers import get_trades_api_helper
from logger_util import logger


def get_leaderboard(request: Request, sleeper_league_id: str) -> json:
    # fetch all trades
    trade_values_result: json = get_trades_api_helper.get_trades(request=request,
                                                                 sleeper_league_id=sleeper_league_id,
                                                                 roster_id='all',
                                                                 transaction_id=None,
                                                                 paginate=False)

    logger.info(f"getting leaderboards on {len(trade_values_result['trades'])} trades")

    return calculate_leaderboard(trade_values_result)


MAX_WORST_TRADE_NET = float('inf')  # Use a constant for max worst trade net
MIN_BEST_TRADE_NET = 0  # Use a constant for min best trade net

def calculate_leaderboard(trades_result: Dict[str, Any]) -> Dict[str, Any]:
    leaderboard_dict = {
        "league_id": trades_result['league_id'],
        "league_name": trades_result['league_name'],
        "league_avatar": trades_result['league_avatar'],
        "league_users": trades_result['league_users'],
        "rankings": []
    }

    temp_rankings = initialize_temp_rankings(trades_result['league_users'])

    for trade in trades_result['trades']:
        if len(trade['roster_ids']) != 2:
            continue

        roster_trade_values = calculate_trade_values(trade)
        update_rankings(temp_rankings, trade, roster_trade_values)

    leaderboard_dict['rankings'] = sorted(temp_rankings.values(), key=lambda x: x['total_net_value'], reverse=True)

    return leaderboard_dict

def initialize_temp_rankings(league_users: List[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    rankings = {}
    for user in league_users:
        rankings[user['roster_id']] = {
            "username": user['user_name'],
            "roster_id": user['roster_id'],
            "user_id": user['user_id'],
            "total_net_value": 0,
            "total_trades": 0,
            "worst_trade_net": MAX_WORST_TRADE_NET,
            "best_trade_net": MIN_BEST_TRADE_NET,
            "worst_trade": None,
            "best_trade": None
        }
    return rankings

def calculate_trade_values(trade: Dict[str, Any]) -> Dict[int, float]:
    roster_id_1, roster_id_2 = trade['roster_ids']
    roster_trade_1 = trade[roster_id_1]
    roster_trade_2 = trade[roster_id_2]

    net_value_1 = roster_trade_1['total_current_value'] - roster_trade_2['total_current_value']
    net_value_2 = roster_trade_2['total_current_value'] - roster_trade_1['total_current_value']

    return {roster_id_1: net_value_1, roster_id_2: net_value_2}

def update_rankings(temp_rankings: Dict[int, Dict[str, Any]], trade: Dict[str, Any], trade_values: Dict[int, float]) -> None:
    for roster_id, net_value in trade_values.items():
        temp_rankings[roster_id]['total_net_value'] += net_value
        temp_rankings[roster_id]['total_trades'] += 1

        if net_value < temp_rankings[roster_id]['worst_trade_net']:
            temp_rankings[roster_id]['worst_trade_net'] = net_value
            temp_rankings[roster_id]['worst_trade'] = trade

        if net_value > temp_rankings[roster_id]['best_trade_net']:
            temp_rankings[roster_id]['best_trade_net'] = net_value
            temp_rankings[roster_id]['best_trade'] = trade

