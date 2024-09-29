import csv
import logging
import os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import django
from django.db import transaction

from populate_player_data_into_db import find_best_match
from util import load_json

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fantasy_trades_app.settings")
django.setup()

# Import your models after Django has been set up
from fantasy_trades_app.models import Players, KtcPlayerValues

# Set up logging
logger = logging.getLogger('data_population_logger2')
logger.setLevel(logging.INFO)

# File handler to log to a file
file_handler = logging.FileHandler('data_population2.log')
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


def bulk_create_players(players_data):
    """Bulk create players in the Players table."""
    Players.objects.bulk_create([
        Players(
            ktc_player_id=data['ktc_player_id'],
            player_name=data['player_name'],
            age=data['age'],
            sleeper_player_id=data['sleeper_player_id'],
            experience=data['experience'],
            number=data['number'],
            position=data['position'],
            team=data['team']
        )
        for data in players_data
    ])


def bulk_create_ktc_values(ktc_values_data):
    """Bulk create KTC values in the KtcPlayerValues table."""
    KtcPlayerValues.objects.bulk_create([
        KtcPlayerValues(
            ktc_player_id=value['ktc_player_id'],
            ktc_value=value['ktc_value'],
            date=value['date']
        )
        for value in ktc_values_data
    ])


def process_csv_file(csv_file, sleeper_players_data_filtered):
    """Process a CSV file and return data to be inserted."""
    player_data_to_create = []
    ktc_values_data_to_create = []

    with open(csv_file, newline='') as csvfile:
        logger.info(f"Processing file: {csv_file.name}")

        reader = csv.DictReader(csvfile)
        sleeper_player_data = None
        for row in reader:
            ktc_player_name = row['NAME'] # name is the same per csv file
            ktc_player_id = int(row['ID']) # id is the same per csv file

            if sleeper_player_data is None:
                sleeper_player_data = find_best_match(ktc_player_name, sleeper_players_data_filtered)

            if sleeper_player_data is None:
                raise Exception(f"Failed to find sleeper data for ({ktc_player_name})")

            player_data_to_create.append({
                'ktc_player_id': ktc_player_id,
                'player_name': ktc_player_name,
                'age': sleeper_player_data.get('age'),
                'sleeper_player_id': sleeper_player_data.get('sleeper_player_id'),
                'experience': sleeper_player_data.get('experience'),
                'number': sleeper_player_data.get('number'),
                'position': sleeper_player_data.get('position'),
                'team': sleeper_player_data.get('team')
            })

            ktc_values_data_to_create.append({
                'ktc_player_id': ktc_player_id,
                'ktc_value': row['VALUE'],
                'date': row['DATE']
            })

    return player_data_to_create, ktc_values_data_to_create


def populate_data():
    logger.info("Starting player data population")
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
        if item.get('fantasy_positions')
           and item.get('position') in ['QB', 'RB', 'WR', 'TE']
           and item.get('player_id')
           and item.get('active') is True
           and item.get('sport')
           and 'nfl' == str(item['sport']).lower()
    ]

    logger.info(f'Number of sleeper players: {len(sleeper_players_data_filtered)}')

    if not sleeper_players_data_filtered:
        raise Exception("No sleeper players available, check filter")

    csv_files = list(csv_directory.glob('*.csv'))
    if not csv_files:
        raise Exception(f"No .csv files found in {csv_directory}")

    player_data_to_create = []
    ktc_values_data_to_create = []

    with ThreadPoolExecutor() as executor:
        future_to_csv = {executor.submit(process_csv_file, csv_file, sleeper_players_data_filtered): csv_file for
                         csv_file in csv_files}
        for future in as_completed(future_to_csv):
            player_data, ktc_values_data = future.result()
            player_data_to_create.extend(player_data)
            ktc_values_data_to_create.extend(ktc_values_data)

    # Bulk insert players and KTC values
    with transaction.atomic():
        bulk_create_players(player_data_to_create)
        bulk_create_ktc_values(ktc_values_data_to_create)

    logger.info("Migrating remaining sleeper players (players without KTC values)")
    remaining_players_data = [
        {
            'ktc_player_id': None,
            'player_name': player['name'],
            'age': player['age'],
            'sleeper_player_id': player['sleeper_player_id'],
            'experience': player['experience'],
            'number': player['number'],
            'position': player['position'],
            'team': player['team']
        }
        for player in sleeper_players_data_filtered
        if not Players.objects.filter(sleeper_player_id=player['sleeper_player_id']).exists()
    ]

    logger.info(f"{Players.objects.count()} players created")

    with transaction.atomic():
        bulk_create_players(remaining_players_data)

    logger.info(f"{KtcPlayerValues.objects.count()} ktc player values created")

if __name__ == '__main__':
    try:
        populate_data()
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)