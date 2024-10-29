import traceback

from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.request import Request

from fantasy_trades_app.settings import VERSION
from frontend_api.api_helpers import get_trades_api_helper, get_leagues_helper, get_leaderboards_helper
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
    return JsonResponse(data={"version": VERSION}, safe=False)


@api_view(['GET'])
def get_leaderboard(request: Request, sleeper_league_id: str) -> JsonResponse:
    try:
        leaderboard_result = get_leaderboards_helper.get_leaderboard(
            request=request,
            sleeper_league_id=sleeper_league_id
        )
        return JsonResponse(data=leaderboard_result, status=200, safe=False)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logger.error(traceback.format_exc())
        return JsonResponse(
            data={"error": f"Error while fetching leaderboard for league '{sleeper_league_id}'"},
            status=500,
            safe=False
        )


@api_view(['GET'])
def get_league_trades(request: Request, sleeper_league_id: str) -> JsonResponse:
    try:
        roster_id = request.GET.get('rosterId', 'all')
        transaction_id = request.GET.get('transactionId', None)
        trades_result = get_trades_api_helper.get_trades(
            request=request,
            sleeper_league_id=sleeper_league_id,
            roster_id=roster_id,
            transaction_id=transaction_id,
            paginate=True
        )
        return JsonResponse(data=trades_result, status=200, safe=False)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logger.error(traceback.format_exc())
        return JsonResponse(
            data={"error": f"Error while fetching trades for league '{sleeper_league_id}'"},
            status=500,
            safe=False
        )


@api_view(['GET'])
def get_trade(request: Request, transaction_id: str) -> JsonResponse:
    try:
        return get_trade_data(transaction_id)
    except Exception as e:
        logger.error("Exception occurred", exc_info=True)
        logger.error(traceback.format_exc())
        return JsonResponse({"error": f"Error while fetching trade {transaction_id}"}, status=500, safe=False)


@api_view(['GET'])
def get_leagues(request: Request, user_name: str) -> JsonResponse:
    try:
        return JsonResponse(data=get_leagues_helper.get_leagues(username=user_name), status=200, safe=False)
    except Exception as e:
        logger.error(msg="Exception occurred", exc_info=True)
        logger.error(msg=traceback.format_exc())
        return JsonResponse(data={"error": "Error while fetching user info"}, status=500, safe=False)
