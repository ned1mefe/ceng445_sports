# 1. Implementation - Correction (55 points):
    # A. General Mehods (20 points)
    # * create(**kw) - 3
    # * list() - 2
    # * listattached(user) - 2
    # * attach(id, user) - 2
    # * detach(id, user) - 2
    # * delete(id) - 4
    # * observer notifications work correctly - 5

    # B. General CRUD (10 points)
    # - For each class:
    #     * Constructor - 5
    #     * delete() - 5

    # * Team Class (2 points)
    #     * __setitem__(key, value), __getattr__(key), __delattr__(key) - 1
    #     * addplayer(name, no), delplayer(name) - 1
    # * Game Class (8 points)
    #     * id(), home(), away() properties - 1
    #     * start(), pause(), resume(), end() - 1
    #     * score(points, team, player) - 1
    #     * stats() - 5
    # * Cup Class (9 points)
    #     * search(tname, group, between) - 4
    #     * __getitem__(gameid) - 1
    #     * gametree() - 1
    #     * standing() - 3
    # * each individual game type logics were implemented correctly - (6 points)


# 2.Unit Tests (20 points)
    # * Write tests that cover all implemented methods and edge cases.

# 3. Individual Understanding (25 points)
    # * You are expected to explain your code during your grading session.
    # * If you cannot adequately explain your work, even if your code functions correctly, 
    # your score for this component will be capped at 40% of the points (i.e., 10 points max).

from pprint import pp
from datetime import datetime
import random
from catalog import Catalog


def main():
    catalog = Catalog()

    print("\n=== TEAM CREATION ===")
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

    print("\n=== CUP CREATION ===")
    cup_id = catalog.create(
        type="cup",
        cup_type="GROUP",
        teams=team_ids,
        interval=(datetime.now(), datetime.now())
    )
    print(f"Cup created with ID: {cup_id}")
    cup = catalog.objectDict[cup_id]
    
    # CATALOG LIST
    print("\nCATALOG LIST\n")
    pp(catalog.list())

    # INITIAL STANDINGS
    print("\n=== INITIAL STANDINGS ===")
    pp(cup.standings())

    print("\n=== SIMULATING GROUP STAGE GAMES ===")
    for group_name, group_cup in cup._groups.items():
        print(f"\n--- GROUP {group_name} ---")
        for game in group_cup._games.values():
            game.start()
            game.score(random.randint(0, 3), game._home_team)
            game.score(random.randint(0, 3), game._away_team)
            game.end()
        print(f"Group {group_name} ended standings:")
        pp(group_cup.standings())

    # Playoffs automatically triggered after all groups end
    if cup._playOffs:
        print("\n=== PLAYOFF STAGE STARTED ===")
        for game in list(cup._playOffs._games.values()):
            game.start()
            game.score(random.randint(0, 4), game._home_team)
            game.score(random.randint(0, 4), game._away_team)
            game.end()
        
        for game in list(l for l in cup._playOffs._games.values() if l.is_ended is False):
            game.start()
            game.score(random.randint(0, 4), game._home_team)
            game.score(random.randint(0, 4), game._away_team)
            game.end()
        
        for game in list(l for l in cup._playOffs._games.values() if l.is_ended is False):
            game.start()
            game.score(random.randint(0, 4), game._home_team)
            game.score(random.randint(0, 4), game._away_team)
            game.end()

    print("\n=== FINAL STANDINGS ===")
    pp(cup.standings())

    print("\n=== Catalog List ===")
    pp(catalog.list())


if __name__ == "__main__":
    main()