from random import shuffle, choice
from models.cup import Cup

class EliminationCup(Cup):

    def __init__(self, teams, interval, rematch_enabled=False):
        super().__init__(teams, interval)
        self._rematch_enabled = rematch_enabled
        self._standings = {team.name : {"Round": 1, "Won": [], "Lost": []} for team in self._teams}
        self._active_teams = self._teams[:]
        self.isPlayoff = False
        
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
                self._create_game(shuffled_teams[i], shuffled_teams[i+1]) 

        if self._rematch_enabled:
            for i in range(0, len(shuffled_teams), 2):
                if i + 1 < len(shuffled_teams):
                    self._create_game(shuffled_teams[i+1], shuffled_teams[i]) 

    def update(self, event):
        if event["type"] == "game_started":
            pass
        elif event["type"] == "game_paused":
            pass
        elif event["type"] == "game_resumed":
            pass
        elif event["type"] == "game_ended":
            self.handleGameEnd(event)
        elif event["type"] == "score":
            pass

    def standings(self):
        return self._standings
    
    def gametree(self):
        pass

    def __str__(self):
        if self.isPlayoff:
            return "PlayOffs"
        if self._rematch_enabled:
            return "Elimination2Cup"
        return "EliminationCup"

    def handleGameEnd(self, event):
        game = event["game"]
        score_home = game.stats()["Home"]["Pts"]
        score_away = game.stats()["Away"]["Pts"]

        if score_home > score_away:
            winner = game.home()
            winner_score = score_home
            loser = game.away() 
            loser_score = score_away

        elif score_away >= score_home: #away is the winner in case of tie
            winner = game.away()
            loser = game.home()
            winner_score = score_away
            loser_score = score_home

        self.standings()[winner.name]["Won"].append((loser.name, winner_score, loser_score))
        self.standings()[loser.name]["Lost"].append((winner.name, loser_score, winner_score))

        if not self._rematch_enabled:
            self.standings()[winner.name]["Round"] += 1
            self._active_teams.remove(loser)

        else:
            matchAndRematch = [
                    g for g in self._games.values()
                    if {g.home().name, g.away().name} == {game.home().name, game.away().name}
                ]
            rematch = matchAndRematch[1] if matchAndRematch[0].id() == game.id() else matchAndRematch[0]

            if (rematch.is_ended):
                rematch_score_home = rematch.stats()["Home"]["Pts"]
                rematch_score_away = rematch.stats()["Away"]["Pts"]

                if score_home + rematch_score_away > score_away + rematch_score_home:
                    loser = game.away()
                    self.standings()[game.home().name]["Round"] += 1
                    self._active_teams.remove(loser)

                elif score_home + rematch_score_away < score_away + rematch_score_home:
                    loser = game.home()
                    self.standings()[game.away().name]["Round"] += 1
                    self._active_teams.remove(loser)

                else: #total score is tied, away score is the tiebreaker
                    
                    if score_away > rematch_score_away:
                        loser = game.home()
                        self.standings()[game.away().name]["Round"] += 1
                        self._active_teams.remove(loser)
                    
                    # also away score is tied, pick randomly
                    else: 
                        loser = choice([game.home(), game.away()])
                        if loser.name == game.home().name:
                            self.standings()[game.away().name]["Round"] += 1
                        else:
                            self.standings()[game.home().name]["Round"] += 1

                        self._active_teams.remove(loser)
                        

        if all(game.is_ended for game in self._games.values()):
            if len(self._active_teams) > 1:
                self._schedule_round()
            else:
                self._notify({"type": "cup_ended", "cup": self, "winner": self._active_teams[0]})
