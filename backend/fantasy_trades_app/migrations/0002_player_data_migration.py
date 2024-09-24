import csv
from pathlib import Path
from django.db import migrations
import logging

# Set up custom logger
logger = logging.getLogger('migration_logger')
file_handler = logging.FileHandler('0002_player_data_migration.log')
file_handler.setLevel(logging.INFO)
logger.addHandler(file_handler)

# Helper function to insert player and player_values
def insert_player_data(apps, schema_editor):
    logger.info("STARTING 0002_player_data_migration")
    print('test')

    players_model = apps.get_model('fantasy_trades_app', 'Players')
    player_values_model = apps.get_model('fantasy_trades_app', 'PlayerValues')

    # Define the directory where your CSV files are located
    csv_directory = Path(__file__).resolve().parent.parent.parent / 'players_data'

    logger.info(csv_directory.absolute())

    # Iterate over all CSV files in the directory
    for csv_file in csv_directory.glob('*.csv'):
        logger.info(csv_file)

        filename = csv_file.stem
        player_name, player_id = filename.split('-')
        player_id = int(player_id)

        # Insert the player into the players table
        player, created = players_model.objects.get_or_create(
            player_id=player_id,
            defaults={'player_name': player_name.replace('_', ' ')}
        )

        # Read the CSV and insert the player values
        with open(csv_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                player_values_model.objects.create(
                    player_id=player,
                    ktc_value=row['VALUE'],
                    date=row['DATE']
                )


# Migration class
class Migration(migrations.Migration):
    dependencies = [
        # Define dependencies here, like initial migrations
        ('fantasy_trades_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_player_data),
    ]
