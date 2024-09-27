import os
import django
import csv
from pathlib import Path
import logging
import re

from util import load_json

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_trades_app.settings")
django.setup()

# Import your models after Django has been set up
from fantasy_trades_app.models import Players, KtcPlayerValues

# Set up logging
logger = logging.getLogger('data_population_logger')
logger.setLevel(logging.INFO)

file_handler = logging.FileHandler('data_population.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)


# Data population function
def populate_data():
    logger.info("Starting player data population")

    # Define the directory where your CSV files are located
    csv_directory = Path(__file__).resolve().parent / 'migration_data/ktc_player_data'

    sleeper_players_data = load_json('/app/migration_data/sleeper_data/get_players.json')
    sleeper_players_data = [
        {
            "name": item["first_name"] + " " + item["last_name"],
            "age": item["age"],
            "sleeper_player_id": item["player_id"],
            "experience": item["years_exp"],  # Double-check if 'years_exp' is correct in the source
            "position": item["position"],
            "number": item["number"],
            "team": item["team"],
            "status": item["status"],
            "sport": item["sport"]
        }
        for item in sleeper_players_data.values()
        if 'status' in item and 'active' == item['status'] and 'sport' in item and 'nfl' == item['sport']
    ]

    # Iterate over all CSV files in the directory
    for csv_file in csv_directory.glob('*.csv'):
        logger.info(f"Processing file: {csv_file}")

        # Read the CSV and insert player values
        with open(csv_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            sleeper_player_data = None
            row_num = 0
            for row in reader:

                row_num = row_num + 1
                player_name = row['NAME']
                ktc_player_id = row['ID']
                if ktc_player_id == 'ID':
                    continue
                player_name_cleansed = re.sub(r'\W+', '', player_name)
                ktc_player_id = int(ktc_player_id)

                # Match sleeper player data
                if sleeper_player_data is None and row_num <= 2:
                    sleeper_player_data = next(
                        (sleeper_player for sleeper_player in sleeper_players_data
                         if player_name_cleansed.lower() == re.sub(r'\W+', '', sleeper_player['name']).lower()),
                        None
                    )

                if not sleeper_player_data:
                    sleeper_player_data = {
                        'age': None,
                        'sleeper_player_id': None,
                        'number': None,
                        'experience': None,
                        'position': None,
                        'team': None
                    }

                # Insert the player into the Players table
                player, created = Players.objects.get_or_create(
                    ktc_player_id=ktc_player_id,
                    defaults={
                        'player_name': player_name,
                        'age': sleeper_player_data['age'],
                        'sleeper_player_id': sleeper_player_data['sleeper_player_id'],
                        'experience': sleeper_player_data['experience'],
                        'number': sleeper_player_data['number'],
                        'position': sleeper_player_data['position'],
                        'team': sleeper_player_data['team']
                    }
                )
                logger.info(f"Player created: {player} (created: {created})")

                KtcPlayerValues.objects.create(
                    player=player,
                    ktc_value=row['VALUE'],
                    date=row['DATE']
                )
                logger.info(f"Inserted player value for {player_name} on {row['DATE']}")

        break


if __name__ == '__main__':
    try:
        populate_data()
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)