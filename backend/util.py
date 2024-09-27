import json

def load_json(json_file_path):
    with open(json_file_path, 'r') as file:
        return json.load(file)