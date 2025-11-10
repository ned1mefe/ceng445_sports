from random import shuffle
from game import Game

class Cup():
    def __init__(self, teams, type, interval):
        self._teams = teams
        if (type not in ["ELIMINATION", "GROUP", "LEAGUE", "ELIMINATION2", "GROUP2", "LEAGUE2"]):
            raise ValueError("Invalid cup type")
        self._type = type
        self._interval = interval
        self._games = {} # gameId -> Game object

        self._initialize_games()

        self.observers = set()

    
    def search(self, tname=None, group=None, between=None):
        results = []

        nameFilter = lambda team: team.name == tname
        groupFilter = lambda team: True # TODO: fix after adding groups
        dateFilter = lambda team: (between[0] <= team.date <= between[1])

        filters = []
    
        if tname is not None:
            filters.append(nameFilter)
        if group is not None:
            if self._type not in ["GROUP", "GROUP2"]:
                raise ValueError("Cannot filter by group in non-group cup type")
            filters.append(groupFilter)
        if between is not None:
            filters.append(dateFilter)

        for team in self._teams:
            if all(f(team) for f in filters): #works fine with empty filter list
                results.append(team)
        
        return results
    
    def __getitem__(self, gameid):
        if gameid in self._games:
            return self._games[gameid]
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

    def _initialize_games(self):
        if self._type in ["ELIMINATION", "ELIMINATION2"]:
            self._initialize_elimination()
        elif self._type in ["GROUP", "GROUP2"]:
            self._initialize_group()
        elif self._type in ["LEAGUE", "LEAGUE2"]:
            self._initialize_league()

    def _initialize_elimination(self): #todo add catalog reference
        shuffled_teams = self._teams[:]
        shuffle(shuffled_teams)
        
        if len(shuffled_teams) % 2 == 1:
            bye_team = shuffled_teams.pop()
            print(f"{bye_team.name} gets a bye to the next round")

        for i in range(0, len(shuffled_teams), 2):
            if i + 1 < len(shuffled_teams):
                game = Game(shuffled_teams[i], shuffled_teams[i + 1])
                self._games[game.id()] = game

        if self._type == "ELIMINATION2":
            for i in range(0, len(shuffled_teams), 2):
                if i + 1 < len(shuffled_teams):
                    game = Game(shuffled_teams[i+1], shuffled_teams[i])
                    self._games[game.id()] = game


    def _initialize_group(self):
        pass


    def _initialize_league(self):
        pass