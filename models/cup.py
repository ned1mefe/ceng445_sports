from random import shuffle
import uuid
from models.game import Game

class Cup():
    def __init__(self, teams, interval):
        self._teams = teams
        self._interval = interval
        self.observers = set()
        self._games = {}  # gameId -> Game object
        self._id = str(uuid.uuid4())

    def search(self, tname=None, group=None, between=None):
        results = []

        nameFilter = lambda game: game.home.name == tname or game.away.name == tname
        groupFilter = lambda game: True # TODO: fix after adding groups
        dateFilter = lambda game: (between[0] <= game.date <= between[1])

        filters = []
    
        if tname is not None:
            filters.append(nameFilter)
        if group is not None:
            if self.description() != "GroupCup":
                raise ValueError("Cannot filter by group in non-group cup type")
            filters.append(lambda team: True)
        if between is not None:
            filters.append(dateFilter)

        for game in self._games.values():
            if all(f(game) for f in filters): #works fine with empty filter list
                results.append(game)

        return results
    
    def __getitem__(self, gameid):
        if gameid in self._games:
            return self._games[gameid]
        else:
            raise KeyError("Game ID not found")
        
    def id(self):
        return self._id
        
    def standings(self):
        pass

    def gametree(self):
        pass

    def initialize_games(self):
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

    def description(self):
        return str(self)
    
    