from models.cup import Cup

class LeagueCup(Cup):

    def __init__(self, cup, teams, interval, rematch_enabled=False):
        super().__init__(cup, teams, interval, rematch_enabled)
        pass
    
    def _schedule_games(self):
        pass
    def standings(self):
        pass
    def gametree(self):
        pass