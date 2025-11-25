from models.cup import Cup
from models.cup_types.elimination_cup import EliminationCup
from models.cup_types.league_cup import LeagueCup

class GroupCup(Cup):

    def __init__(self, teams, interval, rematch_enabled=False):
        super().__init__(teams, interval)
        self._rematch_enabled = rematch_enabled

        self._groupCount = 4 
        self._playOffCount = 8

        if len(teams) < self._groupCount * 2:
            raise ValueError("Not enough teams for GroupCup")
        
        if len(teams) < self._playOffCount:
            raise ValueError("Not enough teams for PlayOffs in GroupCup")

        self._groups = {}  # Group name -> LeagueCup object
        self._playOffs = None

    def initialize_games(self):
        self.initialize_groups()

    def initialize_groups(self):
        shuffled_teams = self._teams[:]
        
        group_names = [chr(i) for i in range(65, 65 + self._groupCount)]  # 'A', 'B', 'C', ...

        group_teams = [[] for _ in range(self._groupCount)]
        for i, team in enumerate(shuffled_teams):
            index = i % self._groupCount
            group_teams[index].append(team)

        self._groups = {name: LeagueCup(group_teams[i], self._interval, self._rematch_enabled) for i, name in enumerate(group_names)}

        for group_name, group_cup in self._groups.items():
            group_cup._groupName = group_name
            group_cup.watch(self)
            group_cup.initialize_games()
            self._games.update(group_cup._games)
            self._notify({"type": "new_group", "cup": self, "group": group_cup})

    def update(self, event):

        if event["type"] == "new_game":
            self._notify(event)

        if event["type"] == "cup_ended":
            if self._playOffs is None:
                self._handleLeagueEnd()
            else:
                self._handlePlayoffEnd(event["winner"])

    def _handleLeagueEnd(self):
        if all(group_cup.league_ended() for group_cup in self._groups.values()):
            self._initialize_playoffs()

    def _handlePlayoffEnd(self, winner):
        self._notify({"type": "cup_ended", "cup": self, "winner": winner})

    def _initialize_playoffs(self):

        k = self._playOffCount // self._groupCount
        qualified_teams = []
        teams_needed_after_loop = self._playOffCount - k*self._groupCount

        subs = []
        for group in self._groups.values():
            standings = group.standings()
            for i in range(k):
                team_name = standings[i][0]
                team = next(t for t in group._teams if t.name == team_name)
                qualified_teams.append(team)

            if teams_needed_after_loop == 0:
                continue

            sub_name, points = standings[k][0], standings[k][1]["Points"]
            sub_team = next(t for t in group._teams if t.name == sub_name)
            subs.append((sub_team, points))

        subs.sort(key=lambda x: -x[1])
        for i in range(teams_needed_after_loop):
            qualified_teams.append(subs[i][0])

        self._playOffs = EliminationCup(qualified_teams, self._interval, self._rematch_enabled)
        self._playOffs.isPlayoff = True
        self._playOffs.watch(self)

        self._notify({"type": "new_group", "cup": self, "group": self._playOffs})

        self._playOffs.initialize_games()

    def standings(self):
        all_standings = {}
        for group_name, group_cup in self._groups.items():
            all_standings[f"Group {group_name}"] = group_cup.standings()

        if self._playOffs is None:
            return all_standings
        
        all_standings["PlayOffs"] = self._playOffs.standings()
        
        return all_standings
    
    def gametree(self):
        pass

    def search(self, tname=None, group=None, between=None):
        if group is not None:
            if group in self._groups:
                return self._groups[group].search(tname=tname, between=between)                
            else:
                raise ValueError("Group not found")
        else:
            return super().search(tname=tname, between=between)
        

    def __str__(self):
        if self._rematch_enabled:
            return "Group2Cup"
        return "GroupCup"