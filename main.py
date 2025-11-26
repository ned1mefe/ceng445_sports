from pprint import pp
from datetime import datetime
import random
import time
from catalog import Catalog
from datetime import timedelta, datetime

def main():
    catalog = Catalog()

    team_names = [
        "Galatasaray", "Fenerbahçe", "Beşiktaş", "Trabzonspor",
        "Bursaspor", "Başakşehir", "Adana Demirspor", "Sivasspor",
        "Antalyaspor", "Konyaspor", "Alanyaspor", "Giresunspor",
        "Hatayspor", "Kayserispor", "Gaziantep FK", "Çaykur Rizespor"
    ]

    team_ids = []
    for name in team_names:
        team_id = catalog.create(type="team", name=name, year=random.randint(1900, 2000), country="Turkey")
        team_ids.append(team_id)

    teams = [catalog.objectDict[i] for i in team_ids]
    for t in teams:
        t.addplayer(f"{t.name}_A", 1)
        t.addplayer(f"{t.name}_B", 2)

    
    cup_id = catalog.create(
        type="cup",
        cup_type="GROUP",
        teams=team_ids,
        interval=(timedelta(days=1)),
    )
    cup = catalog.objectDict[cup_id]


   
    for group_name, group_cup in cup._groups.items():
        print(f"\n--- GROUP {group_name} ---")
        for game in group_cup._games.values():
            # Skip the test game since it is already ended
            if game.is_ended:
                continue  
            game.start()
            game.score(random.randint(0, 3), game._home_team)
            game.score(random.randint(0, 3), game._away_team)
            game.end()
        print(f"Group {group_name} ended standings:")
        pp(group_cup.standings())

    # Playoffs automatically triggered after all groups end
    if cup._playOffs:
        print("\n=== PLAYOFF STAGE STARTED ===")
        
        # We use a loop to handle rounds dynamically as winners advance
        round_counter = 1
        while True:
            # Get current active games that haven't ended
            active_games = [g for g in cup._playOffs._games.values() if not g.is_ended]
            
            if not active_games:
                break
                
            print(f"\n--- Playoff Round {round_counter} ({len(active_games)} games) ---")
            
            for game in active_games:
                game.start()
                game.score(random.randint(0, 4), game._home_team)
                game.score(random.randint(0, 4), game._away_team)
                game.end()
            
            # Check if cup has ended (only 1 active team left) or no new games generated
            if len(cup._playOffs._active_teams) <= 1:
                break
            
            round_counter += 1


    print("\n=== Search ===")
    results = cup.search(group="C")
    if results:
        for i in results:
            print(i.description())
    else:
        print("No games found for Group C.")
    print()
    print()


    print("\n=== Search ===")
    results = cup.search(group="D")
    if results:
        for i in results:
            print(i.description())
    else:
        print("No games found for Group D.")
    print()
    print()

    print("\n=== FINAL STANDINGS ===")
    pp(cup.standings())


if __name__ == "__main__":
    main()