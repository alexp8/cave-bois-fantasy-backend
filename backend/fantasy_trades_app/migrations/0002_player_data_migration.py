import csv
from pathlib import Path
from django.db import migrations


# Helper function to insert player and player_values
def insert_player_data(apps, schema_editor):
    players_model = apps.get_model('fantasy_trades_app', 'Players')
    player_values_model = apps.get_model('fantasy_trades_app', 'PlayerValues')

    # Define the directory where your CSV files are located
    csv_directory = Path(__file__).parent.parent / 'players_data'

    # Iterate over all CSV files in the directory
    for csv_file in csv_directory.glob('*.csv'):

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
