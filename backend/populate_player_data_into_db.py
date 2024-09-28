import os
import django
import csv
from pathlib import Path
import logging
import re
from rapidfuzz import fuzz, process
from util import load_json

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_trades_app.settings")
django.setup()

# Import your models after Django has been set up
from fantasy_trades_app.models import Players, KtcPlayerValues

# Set up logging
logger = logging.getLogger('data_population_logger')
logger.setLevel(logging.INFO)

# File handler to log to a file
file_handler = logging.FileHandler('data_population.log')
file_handler.setLevel(logging.INFO)

# Console handler to log to console (stdout)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Add formatters for both handlers (optional but recommended)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)


# Function to cleanse player name
def cleanse_player_name(name):
    # Remove all non-alphanumeric characters (including spaces) and convert to lowercase
    return re.sub(r'[^a-zA-Z]', '', name).lower()


def find_best_match(ktc_player_name, sleeper_players_data):

    ktc_player_name_cleansed = cleanse_player_name(ktc_player_name)

    sleeper_names = [cleanse_player_name(player['name']) for player in sleeper_players_data]

    best_match = process.extractOne(ktc_player_name_cleansed, sleeper_names, score_cutoff=80)

    if best_match is None:
        return None

    best_match_name, score, index = best_match

    return next(
        (sleeper_player for sleeper_player in sleeper_players_data
         if cleanse_player_name(sleeper_player['name']) == best_match_name),
        None
    )


def populate_data():
    logger.info("Starting player data population")

    # Define the directory where your CSV files are located
    csv_directory = Path(__file__).resolve().parent / 'migration_data/ktc_player_data'

    sleeper_players_data = load_json('/app/migration_data/sleeper_data/get_players.json')

    sleeper_players_data_filtered = [
        {
            "name": item.get('full_name', 'Unknown'),
            "first_name": item.get('first_name', 'Unknown'),
            "last_name": item.get('last_name', 'Unknown'),
            "age": item.get('age', None),
            "sleeper_player_id": item.get('player_id', None),
            "experience": item.get('years_exp', None),
            "position": item.get('position', None),
            "number": item.get('number', None),
            "team": item.get('team', None),
            "sport": item.get('sport', None),
        }
        for item in sleeper_players_data.values()
        if item.get('fantasy_positions')  # Check if 'fantasy_positions' exists and is not None
           and item.get('position') in ['QB', 'RB', 'WR', 'TE']
           and item.get('player_id')  # Ensure 'player_id' exists
           and item.get('active') is True  # Ensure 'active' is True
           and item.get('sport')  # Check if 'sport' exists
           and 'nfl' == str(item['sport']).lower()  # Ensure sport is 'nfl'
    ]

    logger.info(f'Number of sleeper players: {len(sleeper_players_data_filtered)}')

    if len(sleeper_players_data_filtered) == 0:
        raise Exception(f"No sleeper players available, check filter")

    # Iterate over all CSV files in the directory
    csv_file_count = sum(1 for _ in csv_directory.glob('*.csv'))

    if csv_file_count == 0:
        raise Exception(f"No .csv files found in {csv_directory}")

    count = 1
    for csv_file in csv_directory.glob('*.csv'):

        logger.info(f"Processing file ({count} of {csv_file_count}): {csv_file.name}")
        count = count + 1

        # Read the CSV and insert player values
        with open(csv_file, newline='') as csvfile:

            reader = csv.DictReader(csvfile)
            sleeper_player_data = None
            for row in reader:

                ktc_player_name = row['NAME']
                ktc_player_id = int(row['ID'])

                # Match sleeper player data
                if sleeper_player_data is None and '202' not in ktc_player_name:
                    sleeper_player_data = find_best_match(ktc_player_name, sleeper_players_data_filtered)

                    if sleeper_player_data is None:
                        raise Exception(f"Failed to find sleeper data for ({ktc_player_name})")

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
                        'player_name': ktc_player_name,
                        'age': sleeper_player_data['age'],
                        'sleeper_player_id': sleeper_player_data['sleeper_player_id'],
                        'experience': sleeper_player_data['experience'],
                        'number': sleeper_player_data['number'],
                        'position': sleeper_player_data['position'],
                        'team': sleeper_player_data['team']
                    }
                )

                KtcPlayerValues.objects.get_or_create(
                    ktc_player_id=player,
                    ktc_value=row['VALUE'],
                    date=row['DATE']
                )


if __name__ == '__main__':
    try:
        populate_data()
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
