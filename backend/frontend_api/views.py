import traceback

from django.http import JsonResponse
from rest_framework.decorators import api_view

from fantasy_trades_app.settings import VERSION
from frontend_api.api_helpers import get_trades_api_helper, get_leagues_helper
from frontend_api.api_helpers.get_trade_api_helper import get_trade_data
from logger_util import logger


@api_view(['GET'])
def get_players_from_sleeper(request):
    None


@api_view(['GET'])
def get_players_from_sleeper_like(request, search_str):
    None


@api_view(['GET'])
def get_version(request):
    return JsonResponse({"version": VERSION}, safe=False)


@api_view(['GET'])
def get_league_trades(request, sleeper_league_id):

    try:
        roster_id = request.GET.get('rosterId', None)
        return get_trades_api_helper.get_trades(request, sleeper_league_id, roster_id)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logger.error(traceback.format_exc())
        return JsonResponse(
            {"error": f"Error while fetching trades for league '{sleeper_league_id}'"},
            status=500,
            safe=False
        )


@api_view(['GET'])
def get_trade(request, transaction_id):

    try:
        return get_trade_data(transaction_id)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logger.error(traceback.format_exc())
        return JsonResponse({"error": f"Error while fetching trade {transaction_id}"}, status=500, safe=False)


@api_view(['GET'])
def get_leagues(request, user_name):

    try:
        return JsonResponse(get_leagues_helper.get_leagues(user_name), status=200, safe=False)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logger.error(traceback.format_exc())
        return JsonResponse({"error": "Error while fetching user info"}, status=500, safe=False)