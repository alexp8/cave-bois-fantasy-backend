import csv
from pathlib import Path
from django.db import migrations
import logging

# Use the logger from the global settings
logger = logging.getLogger('django')

# Helper function to insert player and player_values
def insert_player_data(apps, schema_editor):
    logger.info("STARTING 0002_player_data_migration")

    players_model = apps.get_model('fantasy_trades_app', 'Players')
    player_values_model = apps.get_model('fantasy_trades_app', 'PlayerValues')

    # Define the directory where your CSV files are located
    csv_directory = Path(__file__).resolve().parent.parent.parent / 'player_data'

    logger.info(f"CSV Directory: {csv_directory.absolute()}")
    print(f"CSV Directory: {csv_directory.absolute()}")

    # Inside your insert_player_data function, replace the relevant section with this:
    for csv_file in csv_directory.glob('*.csv'):
        logger.info(f"Processing file: {csv_file}")
        print(f"Processing file: {csv_file}")

        # Read the CSV and insert the player values
        with open(csv_file, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:

                # Insert the player into the players table
                player, created = players_model.objects.get_or_create(
                    player_id=row['ID'],
                    defaults={'player_name': row['NAME']}
                )

                player_values_model.objects.create(
                    player_id=player.player_id,
                    ktc_value=row['VALUE'],
                    date=row['DATE']
                )
                logger.info(f"Inserted player value for {player.player_name} on {row['DATE']}")


# Migration class
class Migration(migrations.Migration):
    dependencies = [
        ('fantasy_trades_app', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(insert_player_data),
    ]
