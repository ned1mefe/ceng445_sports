from models.cup import Cup

class LeagueCup(Cup):

    def __init__(self, teams, interval, rematch_enabled=False):
        super().__init__(teams, interval)
        self._rematch_enabled = rematch_enabled
        pass
    
    def _schedule_games(self):
        pass
    def standings(self):
        pass
    def gametree(self):
        pass

    def initialize_games(self):
        pass


    def __str__(self):
        return "LeagueCup"