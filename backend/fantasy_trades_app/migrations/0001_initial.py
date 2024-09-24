from django.db import migrations, models

class Migration(migrations.Migration):

    initial = True

    operations = [
        # Create table 'players'
        migrations.CreateModel(
            name='Players',
            fields=[
                ('player_id', models.AutoField(primary_key=True, serialize=False)),  # Auto-increment primary key
                ('player_name', models.CharField(max_length=255)),  # Player name column
            ],
        ),

        # Create table 'player_values' with a foreign key to 'players'
        migrations.CreateModel(
            name='PlayerValues',
            fields=[
                ('id', models.BigAutoField (auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),  # Auto-increment primary key
                ('ktc_value', models.IntegerField()),  # Integer field for ktc_value
                ('date', models.DateField()),  # Date field
                ('player', models.ForeignKey(on_delete=models.CASCADE, to='fantasy_trades_app.Players')),  # Foreign key to 'Players' (use 'player')
            ],
        ),
        # Add a unique constraint for player and date in 'player_values'
        migrations.AlterUniqueTogether(
            name='PlayerValues',
            unique_together={('player', 'date')},
        ),
    ]
