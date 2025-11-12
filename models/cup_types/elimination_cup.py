from random import shuffle
from models.cup import Cup

class EliminationCup(Cup):

    def __init__(self, cup, teams, interval, rematch_enabled=False):
        super().__init__(cup, teams, interval, rematch_enabled)
        pass

    def _schedule_games(self):
        shuffled_teams = self._teams[:]
        shuffle(shuffled_teams)
        
        if len(shuffled_teams) % 2 == 1:
            bye_team = shuffled_teams.pop()
            print(f"{bye_team.name} gets a bye to the next round")

        for i in range(0, len(shuffled_teams), 2):
            if i + 1 < len(shuffled_teams):
                self._create_game(shuffled_teams[i], shuffled_teams[i+1], self._interval[0]) #placeholder datetime

        if self._rematch_enabled:
            for i in range(0, len(shuffled_teams), 2):
                if i + 1 < len(shuffled_teams):
                    self._create_game(shuffled_teams[i+1], shuffled_teams[i], self._interval[0]) #placeholder datetime


    def standings(self):
        pass
    def gametree(self):
        pass