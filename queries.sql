SELECT * FROM public.django_migrations
ORDER BY id ASC 

delete FROM public.django_migrations
where id = 20

SELECT * FROM public.fantasy_trades_app_players;

SELECT * FROM public.fantasy_trades_app_ktcplayervalues
ORDER BY id ASC;

--- DELETE
DELETE FROM public.fantasy_trades_app_players;
DELETE FROM public.fantasy_trades_app_ktcplayervalues;

-- DROPS
-- DROP TABLE public.fantasy_trades_app_ktcplayervalues;
-- DROP TABLE public.fantasy_trades_app_players;






