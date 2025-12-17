from random import shuffle
import uuid
from class_library.models.game import Game
from datetime import datetime

class Cup():
    def __init__(self, teams, interval):
        self._teams = teams
        self._interval = interval
        self.observers = set()
        self._games = {}  # gameId -> Game object
        self._id = str(uuid.uuid4())
        self._start_date = datetime.now()
        self._last_game_date = self._start_date

    def search(self, tname=None, group=None, between=None):
        results = []

        nameFilter = lambda game: game.home().name == tname or game.away().name == tname
        
        dateFilter = lambda game: (between[0] <= game._datetime <= between[1])

        filters = []
    
        if tname is not None:
            filters.append(nameFilter)
        if group is not None:
            #this is valid, group cup overrides this method
            raise ValueError("Cannot filter by group in non-group cup type")
            
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
        for game in self._games.values():
                game.unwatch(obj)

    def _notify(self, event):
        for obs in self.observers:
            obs.update(event)

    def update(self, event):
        pass
        
    def _create_game(self, team1, team2):
        game_date = self._last_game_date + self._interval
        self._last_game_date = game_date
        game = Game(team1, team2, game_date)
        self._games[game.id()] = game

        game.watch(self)  # Cup observes the game for events

        for obs in self.observers:
            game.watch(obs)  # Cup's observers also observe the game

        self._notify({"type": "new_game", "game": game})  # Notify cup's observers
        return game

    def description(self):
        return str(self)
    
        
    def __getstate__(self):
        return {k: v for (k, v) in self.__dict__.items() if k != "observers"}
    
    
    def __setstate__(self, state):
        self.observers = set()
        self.__dict__.update(state)

        self._restore_observers()

    def _restore_observers(self):
        for game in self._games.values():
            game.watch(self)
    
    