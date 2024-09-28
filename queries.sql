-- migrations
SELECT * FROM public.django_migrations
ORDER BY id ASC 

-- all players
SELECT * FROM public.fantasy_trades_app_players;

-- id
SELECT * FROM public.fantasy_trades_app_players
where sleeper_player_id = 8151;

-- player name
SELECT * FROM public.fantasy_trades_app_players
where lower(player_name) like '%walker%';

-- players missing sleeper info
SELECT * FROM public.fantasy_trades_app_players
where sleeper_player_id is null
and player_name not like '%202%';

-- ktc values
SELECT * FROM public.fantasy_trades_app_ktcplayervalues
ORDER BY id ASC;

--- DELETE
DELETE FROM public.fantasy_trades_app_players;
DELETE FROM public.fantasy_trades_app_ktcplayervalues;

DELETE FROM public.fantasy_trades_app_players
where sleeper_player_id is null
and player_name not like '%202%';

DELETE FROM fantasy_trades_app_ktcplayervalues
WHERE ktc_player_id IN (
    SELECT ktc_player_id 
    FROM fantasy_trades_app_players
    WHERE sleeper_player_id IS NULL
	and player_name not like '%202%'
);


-- DROPS
-- DROP TABLE public.fantasy_trades_app_ktcplayervalues;
-- DROP TABLE public.fantasy_trades_app_players;






