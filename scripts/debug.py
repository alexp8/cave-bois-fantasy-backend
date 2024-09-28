import json

def main():
    sleeper_players_data = None
    with open('../migration_data/sleeper_data/get_players.json', 'r') as file:
        sleeper_players_data = json.load(file)

    if len(sleeper_players_data) == 0:
        raise Exception(f"No sleeper players available")

    sleeper_players_data_filtered = [
        {
            "name": item.get('full_name', 'Unknown'),
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
           and 'DEF' not in item['fantasy_positions']  # Exclude defense
           and item.get('player_id')  # Ensure 'player_id' exists
           and item.get('active') is True  # Ensure 'active' is True
           and item.get('sport')  # Check if 'sport' exists
           and 'nfl' == str(item['sport']).lower()  # Ensure sport is 'nfl'
    ]

    if len(sleeper_players_data_filtered) == 0:
        raise Exception(f"No sleeper players available, check filter")

    print(f"{len(sleeper_players_data_filtered)}")

if __name__ == "__main__":
    main()
