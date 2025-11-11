from random import shuffle
from game import Game
from cup_types.group_cup import GroupCup
from cup_types.league_cup import LeagueCup
from cup_types.elimination_cup import EliminationCup

class Cup():
    def __init__(self, teams, type, interval):
        self._teams = teams
        if (type not in ["ELIMINATION", "GROUP", "LEAGUE", "ELIMINATION2", "GROUP2", "LEAGUE2"]):
            raise ValueError("Invalid cup type")
        
        self._interval = interval
        self.observers = set()

        if type in ["ELIMINATION", "ELIMINATION2"]:
            self._cup_type = EliminationCup(self, teams, rematch_enabled=(type.endswith("2")))

        elif type in ["GROUP", "GROUP2"]:
            self._cup_type = GroupCup(self, teams, rematch_enabled=(type.endswith("2")))
            
        elif type in ["LEAGUE", "LEAGUE2"]:
            self._cup_type = LeagueCup(self, teams, rematch_enabled=(type.endswith("2")))   

    
    def search(self, tname=None, group=None, between=None):
        results = []

        nameFilter = lambda team: team.name == tname
        groupFilter = lambda team: True # TODO: fix after adding groups
        dateFilter = lambda team: (between[0] <= team.date <= between[1])

        filters = []
    
        if tname is not None:
            filters.append(nameFilter)
        if group is not None:
            if not isinstance(self._cup_type, GroupCup):
                raise ValueError("Cannot filter by group in non-group cup type")
            filters.append(groupFilter)
        if between is not None:
            filters.append(dateFilter)

        for team in self._teams:
            if all(f(team) for f in filters): #works fine with empty filter list
                results.append(team)
        
        return results
    
    def __getitem__(self, gameid):
        if gameid in self._cup_type._games:
            return self._cup_type._games[gameid]
        else:
            raise KeyError("Game ID not found")
        
    def standings(self):
        pass

    def gametree(self):
        pass

    def watch(self, obj, **searchparams):
        if obj:
            self.observers.add(obj)

            games = self.search(**searchparams)
            for game in games:
                game.watch(obj)

    def unwatch(self, obj):
        self.observers.discard(obj) #does not raise error if obj not found

    def _notify(self, event):
        for obs in self.observers:
            obs.update(event)

    def update(self, event):
        if event["type"] == "game_started":
            pass
        elif event["type"] == "game_paused":
            pass
        elif event["type"] == "game_resumed":
            pass
        elif event["type"] == "game_ended":
            pass
        elif event["type"] == "score":
            pass
        
