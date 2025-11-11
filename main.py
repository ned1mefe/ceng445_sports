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
from models.game import Game
from models.team import Team
import datetime
# --- 1. Create Teams ---
print("--- 1. Setting up teams ---")
team1 = Team("Fenerbahçe Beko")
team1.addplayer("Baldwin IV", 1)
team1.addplayer("Biberoviç", 2)
team1.addplayer("Tucker", 3)

team2 = Team("Anadolu Efes")
team2.addplayer("Larkin", 10)
team2.addplayer("Osmani", 11)
team2.addplayer("Bobua", 12)

print(f"Home: {team1.name} with players: {list(team1.players.keys())}")
print(f"Away: {team2.name} with players: {list(team2.players.keys())}")

# --- 2. Create Game ---
print("\n--- 2. Creating game ---")
game_time = datetime.datetime.now()
game = Game(team1, team2, game_time)
print(f"Game created with ID: {game._id}")

# --- 3. Run Game and Score ---
print("\n--- 3. Running game ---")
game.start()
print("Game started.")

try:
    game.score(2, team2, "Larkin")
    pp(game.stats())
    game.score(3, team1, "Biberoviç")
    pp(game.stats())
    game.score(2, team1, "Baldwin IV")
    pp(game.stats())
    game.score(1, team2, "Larkin")
    pp(game.stats())
    game.score(3, team2, "Bobua")
    pp(game.stats())
except ValueError as e:
    print(f"An error occurred during scoring: {e}")

game.end()
print("Game ended.")

# --- 4. Print Stats ---
print("\n--- 4. Final Stats ---")
pp(game.stats())