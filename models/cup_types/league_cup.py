from models.cup import Cup
from random import shuffle

class LeagueCup(Cup):

    def __init__(self, teams, interval, rematch_enabled=False):
        super().__init__(teams, interval)
        self._rematch_enabled = rematch_enabled
        self._table = {team.name : {"Won": 0, "Draw": 0, "Lost": 0, "Scored": 0, "Conceded": 0, "Average": 0, "Points": 0} for team in self._teams}
        
        self.pointsWin = 2
        self.pointsDraw = 1
        self.pointsLoss = 0
        pass
    
    def standings(self):
        return self.score_based_sorting()

    def gametree(self):
        pass

    # called once 
    def initialize_games(self):
        shuffled_teams = self._teams[:]
        shuffle(shuffled_teams) # shuffled for unfair home advantage in League1 format

        for i, t1 in enumerate(shuffled_teams):
            for j, t2 in enumerate(shuffled_teams):
                if j > i:
                    self._create_game(t1, t2, self._interval)
        
        # home - away switched so it is balanced 
        if self._rematch_enabled:
            for i, t1 in enumerate(shuffled_teams):
                for j, t2 in enumerate(shuffled_teams):
                    if j > i:
                        self._create_game(t2, t1, self._interval)
        pass

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


    def handleGameEnd(self, event):
        game = event["game"]
        score_home = game.stats()["Home"]["Pts"]
        score_away = game.stats()["Away"]["Pts"]

        if score_home > score_away:
            winner = game._home_team
            winner_score = score_home
            loser = game._away_team
            loser_score = score_away

        elif score_away > score_home: 
            winner = game._away_team
            loser = game._home_team
            winner_score = score_away
            loser_score = score_home

        else:
            # draw
            winner = None
            loser = None
            draw_home = game._home_team.name 
            draw_away = game._away_team.name 
            draw_score = score_home
        
        # not a draw
        if winner:
            self._table[winner.name]["Won"] += 1
            self._table[winner.name]["Scored"] += winner_score
            self._table[winner.name]["Conceded"] += loser_score
            self._table[winner.name]["Average"] = self._table[winner.name]["Scored"] - self._table[winner.name]["Conceded"]
            self._table[winner.name]["Points"] += self.pointsWin

            self._table[loser.name]["Lost"] += 1
            self._table[loser.name]["Scored"] += loser_score
            self._table[loser.name]["Conceded"] += winner_score
            self._table[loser.name]["Average"] = self._table[loser.name]["Scored"] - self._table[loser.name]["Conceded"]
            self._table[loser.name]["Points"] += self.pointsLoss
        
        # there is a draw
        else:
            self._table[draw_home]["Draw"] += 1
            self._table[draw_home]["Scored"] += draw_score
            self._table[draw_home]["Conceded"] += draw_score
            self._table[draw_home]["Points"] += self.pointsDraw

            self._table[draw_away]["Draw"] += 1
            self._table[draw_away]["Scored"] += draw_score
            self._table[draw_away]["Conceded"] += draw_score
            self._table[draw_away]["Points"] += self.pointsDraw


        # all games are ended 
        if all(game.is_ended for game in self._games.values()):
            sorted_dict = self.score_based_sorting()
            print(f"League Winner: {sorted_dict[0][0]}")

           
    def score_based_sorting(self):
        table_items = self._table.items()
        sorted_items = sorted(
            table_items,
            key=lambda item: (-item[1]["Points"], -item[1]["Average"]),
        )
        
        return sorted_items

    def __str__(self):
        if self._rematch_enabled:
            return "League2Cup"
        return "LeagueCup"