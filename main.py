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
from models.cup_types.elimination_cup import EliminationCup
from models.team import Team 

class DummyObserver:
    def __init__(self):
        self.events = []

    def update(self, event):
        self.events.append(event)

def main():

    observer = DummyObserver()
    sample_teams = [Team(f"Team{i}") for i in range(1, 5)]
    for t in sample_teams:
        t.addplayer(f"Player{t.name}_A",1)
        t.addplayer(f"Player{t.name}_B",2)
    elim = EliminationCup(sample_teams, (datetime(2025, 1, 1), datetime(2025, 12, 31)))

    elim.watch(observer)
    elim.initialize_games()

    i = 0
    while not observer.events or observer.events[-1]["type"] != "cup_ended":
        game = list(elim._games.values())[i]
        game.score(10, game.home(), list(game.home().players.keys())[0])
        game.score(5, game.away(), list(game.away().players.keys())[0])
        game.end()
        i += 1

    standings = elim.standings()

    print("Standings after one game ended:")
    pp(standings)


if __name__ == "__main__":
    main()