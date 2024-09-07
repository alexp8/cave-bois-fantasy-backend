import json


def main():

    picks = []
    for year in range(2021, 2029):
        for round in range(1,6):
            suffix = "st"
            if round == 2:
                suffix = "nd"
            elif round == 3:
                suffix = "rd"
            elif round == 4 or round == 5:
                suffix = "th"
            picks.append(f"{str(year)} {round}{suffix} round pick")

    json_picks = json.dumps(picks, indent=4)
    print(json_picks)

if __name__ == "__main__":
    main()
