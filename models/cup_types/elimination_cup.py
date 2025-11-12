from random import shuffle
from models.cup import Cup

class EliminationCup(Cup):

    def __init__(self, teams, interval, rematch_enabled=False):
        super().__init__(teams, interval)
        self._rematch_enabled = rematch_enabled
        self._standings = {team.name : {"Round": 1, "Won": [], "Lost": []} for team in self._teams}
        self._active_teams = self._teams[:]
        
    def initialize_games(self):
        self._schedule_round()

    def _schedule_round(self):
        shuffled_teams = self._active_teams[:]
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

    def update(self, event):
        if event["type"] == "game_started":
            pass
        elif event["type"] == "game_paused":
            pass
        elif event["type"] == "game_resumed":
            pass
        elif event["type"] == "game_ended":
            game = event["game"]
            score_home = game.stats()["Home"]["Pts"]
            score_away = game.stats()["Away"]["Pts"]

            if score_home > score_away:
                winner = game.home
                winner_score = score_home
                loser = game.away
                loser_score = score_away

            elif score_away > score_home:
                winner = game.away
                loser = game.home
                winner_score = score_away
                loser_score = score_home

            self.standings()[winner.name]["Won"].append((loser.name, winner_score, loser_score))
            self.standings()[loser.name]["Lost"].append((winner.name, loser_score, winner_score))

            self._active_teams.remove(loser)

            if all(game.is_ended for game in self._games.values()):
                if len(self._active_teams) > 1:
                    for team in self._active_teams:
                        self.standings()[team.name]["Round"] += 1
                    self._schedule_round()

                else:
                    print(f"Tournament Winner: {self._active_teams[0].name}")

        elif event["type"] == "score":
            pass

    def standings(self):
        return self._standings
    
    def gametree(self):
        pass

    def __str__(self):
        return "EliminationCup"