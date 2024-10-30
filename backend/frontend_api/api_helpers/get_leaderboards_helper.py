import json

from requests import Request

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

    return calculate_leaderboard(trade_values_result['league_users'], trade_values_result['trades'])


def calculate_leaderboard(league_users: dict, trades: list) -> dict:
    # leaderboard dict
    leaderboard_dict = {}

    # init leaderboard_dict
    for league_user in league_users:
        leaderboard_dict[league_user['roster_id']] = {
            "username": league_user['user_name'],
            "roster_id": league_user['roster_id'],
            "user_id": league_user['user_id'],
            "total_net_value": 0,
            "total_trades": 0,
            "worst_trade_net": 1000,
            "best_trade_net": 0,
            "worst_trade": None,
            "best_trade": None
        }

    for trade in trades:

        if len(trade['roster_ids']) != 2:
            continue

        roster_id_1: int = trade['roster_ids'][0]
        roster_id_2: int = trade['roster_ids'][1]

        roster_trade_1 = trade[roster_id_1]
        roster_trade_2 = trade[roster_id_2]

        # calculate net value gained from the trade
        roster_trade_1_net_value = roster_trade_1['total_current_value'] - roster_trade_2['total_current_value']
        roster_trade_2_net_value = roster_trade_2['total_current_value'] - roster_trade_1['total_current_value']

        # add net_value total
        leaderboard_dict[roster_id_1]['total_net_value'] += roster_trade_1_net_value
        leaderboard_dict[roster_id_2]['total_net_value'] += roster_trade_2_net_value

        # worst trade check
        if roster_trade_1_net_value <= leaderboard_dict[roster_id_1]['worst_trade_net']:
            leaderboard_dict[roster_id_1]['worst_trade_net'] = roster_trade_1_net_value
            leaderboard_dict[roster_id_1]['worst_trade'] = trade

        if roster_trade_2_net_value <= leaderboard_dict[roster_id_2]['worst_trade_net']:
            leaderboard_dict[roster_id_2]['worst_trade_net'] = roster_trade_2_net_value
            leaderboard_dict[roster_id_2]['worst_trade'] = trade

        # best trade check
        if roster_trade_1_net_value > leaderboard_dict[roster_id_1]['best_trade_net']:
            leaderboard_dict[roster_id_1]['best_trade_net'] = roster_trade_1_net_value
            leaderboard_dict[roster_id_1]['best_trade'] = trade

        if roster_trade_2_net_value > leaderboard_dict[roster_id_2]['best_trade_net']:
            leaderboard_dict[roster_id_2]['best_trade_net'] = roster_trade_2_net_value
            leaderboard_dict[roster_id_2]['best_trade'] = trade

        leaderboard_dict[roster_id_1]['total_trades'] += 1
        leaderboard_dict[roster_id_2]['total_trades'] += 1

    return leaderboard_dict
