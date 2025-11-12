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
from catalog import Catalog
from datetime import datetime
from models.game import Game  # Bu sınıfın Game(home, away, datetime) constructor’ı olduğunu varsayıyorum

def main():
    catalog = Catalog()

    print("=== TEAM CREATION ===")
    team1_id = catalog.create(type="team", name="Galatasaray", year=1905, country="Turkey")
    team2_id = catalog.create(type="team", name="Fenerbahçe", year=1907, country="Turkey")
    team3_id = catalog.create(type="team", name="Beşiktaş", year=1903, country="Turkey")

    print("Teams created with IDs:")
    print(team1_id, team2_id, team3_id)

    print("\n=== ATTACH TEAMS TO USER ===")
    user_id = "user123"
    catalog.attach(team1_id, user_id)
    catalog.attach(team2_id, user_id)
    print(f"Attached teams to {user_id}: {catalog.listattached(user_id)}")

    print("\n=== CUP CREATION ===")
    cup_id = catalog.create(
        type="cup",
        cup_type="ELIMINATION",
        teams=[team1_id, team2_id, team3_id],
        interval=(datetime.now(), datetime.now())
    )
    print(f"Cup created with ID: {cup_id}")

    print("\n=== CATALOG LIST ===")
    print(catalog.list())

    print("\n=== CREATE A GAME DIRECTLY ===")
    game_id = catalog.create(
        type="game",
        home=team1_id,
        away=team2_id,
        datetime=datetime.now()
    )
    print(f"Game created with ID: {game_id}")

    print("\n=== ATTACH GAME AND LIST ===")
    catalog.attach(game_id, user_id)
    print(f"User’s attached objects: {catalog.listattached(user_id)}")

    print("\n=== DELETE TEST ===")
    try:
        catalog.delete(team3_id)
        print("Team3 deleted successfully.")
    except ValueError:
        print("Cannot delete team3: attached or not found.")

    print("\n=== CUP EVENT SIMULATION ===")
    # Simulate cup generating a new game and notifying catalog
    fake_game = Game(
        catalog.objectDict[team1_id],
        catalog.objectDict[team2_id],
        datetime.now()
    )
    event = {"type": "new_game", "game": fake_game}
    catalog.update(event)
    print("After cup event, catalog now contains:")
    print(catalog.list())

if __name__ == "__main__":
    main()