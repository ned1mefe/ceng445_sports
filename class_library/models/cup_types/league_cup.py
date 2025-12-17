from class_library.models.cup import Cup
from random import shuffle

class LeagueCup(Cup):

    def __init__(self, teams, interval, rematch_enabled=False):
        super().__init__(teams, interval)
        self._rematch_enabled = rematch_enabled
        self._table = {team.name : {"Won": 0, "Draw": 0, "Lost": 0, "Scored": 0, "Conceded": 0, "Diff": 0, "Points": 0} for team in self._teams}
        
        self._groupName = None
        self.pointsWin = 2
        self.pointsDraw = 1
        self.pointsLoss = 0
    
    def standings(self):
        return self.score_based_sorting()

    def gametree(self):
        pass

    def initialize_games(self):
        rotation_list = self._teams[:]
        shuffle(rotation_list)
        
        if len(rotation_list) % 2 != 0:
            rotation_list.append(None)

        num_teams = len(rotation_list)
        num_rounds = num_teams - 1
        half_size = num_teams // 2
        
        all_rounds = []

        for _ in range(num_rounds):
            this_round_matches = []
            
            for i in range(half_size):
                t1 = rotation_list[i]
                t2 = rotation_list[num_teams - 1 - i]

                if t1 is not None and t2 is not None:
                    this_round_matches.append((t1, t2))
            
            all_rounds.append(this_round_matches)
            rotation_list.insert(1, rotation_list.pop())

        if self._rematch_enabled:
            second_half = []
            for round_matches in all_rounds:
                rematch_round = []
                for home, away in round_matches:
                    rematch_round.append((away, home)) 
                second_half.append(rematch_round)
            
            all_rounds.extend(second_half)
        
        
        for round_matches in all_rounds:
            for home, away in round_matches:
                self._create_game(home, away)
            
            ## Only increase time AFTER the whole round is scheduled
            # current_time_offset += self._interval

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
            self._table[winner.name]["Diff"] = self._table[winner.name]["Scored"] - self._table[winner.name]["Conceded"]
            self._table[winner.name]["Points"] += self.pointsWin

            self._table[loser.name]["Lost"] += 1
            self._table[loser.name]["Scored"] += loser_score
            self._table[loser.name]["Conceded"] += winner_score
            self._table[loser.name]["Diff"] = self._table[loser.name]["Scored"] - self._table[loser.name]["Conceded"]
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
            self._notify({"type": "cup_ended", "cup": self, "winner": sorted_dict[0][0]})

           
    def score_based_sorting(self):
        table_items = self._table.items()
        sorted_items = sorted(
            table_items,
            key=lambda item: (-item[1]["Points"], -item[1]["Diff"]),
        )
        return sorted_items
    
    def league_ended(self):
        return all(game.is_ended for game in self._games.values())

    def __str__(self):
        if self._groupName:
            return f"Group :{self._groupName}"
        if self._rematch_enabled:
            return "League2Cup"
        return "LeagueCup"
    