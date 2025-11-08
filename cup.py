class Cup():
    def __init__(self, teams, type, interval):
        self._teams = teams
        if (type not in ["ELIMINATION", "GROUP", "LEAGUE"]):
            raise ValueError("Invalid cup type")
        self._type = type
        self._interval = interval
        self._games = {} # gameId -> Game object

        self.observers = set

    
    def search(self, tname=None, group=None, between=None):
        results = []

        nameFilter = lambda team: team.name == tname
        groupFilter = lambda team: team.group == group
        dateFilter = lambda team: (between[0] <= team.date <= between[1])

        filters = []
    
        if tname is not None:
            filters.append(nameFilter)
        if group is not None:
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