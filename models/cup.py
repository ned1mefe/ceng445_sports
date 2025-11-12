from random import shuffle
import uuid
from game import Game
from cup_types.group_cup import GroupCup

class Cup():
    def __init__(self, teams, interval, rematch_enabled=False):
        self._teams = teams
        self._interval = interval
        self.observers = set()
        self._games = {}  # gameId -> Game object
        self._id = str(uuid.uuid4())


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
        
    def id(self):
        return self._id
        
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
        
    def _create_game(self, team1, team2, datetime):
        game = Game(team1, team2, datetime)
        self._games[game.id()] = game

        game.watch(self)  # Cup observes the game for events

        self._notify({"type": "new_game", "game": game})  # Notify cup's observers
        return game
    
    