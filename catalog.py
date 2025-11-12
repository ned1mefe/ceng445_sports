import uuid
from models.cup import Cup
from models.cup_types.elimination_cup import EliminationCup
from models.cup_types.group_cup import GroupCup
from models.cup_types.league_cup import LeagueCup
from models.team import Team
from models.game import Game

class Catalog:
    def __init__(self):
        self.attachDict = {} # user (or userID) -> [objectId]
        self.objectDict = {} # objectId -> object

    def _resolve_team(self, val):
        if val in self.objectDict:
            resolved = self.objectDict[val]
            if isinstance(resolved, Team):
                return resolved
            else:
                raise ValueError(f"Object with id {val} is not a Team")

        raise ValueError("Cannot resolve team: must be an active team id")

    def _create_team(self, **kw):
        return Team(kw['name'], kw['year'], kw['country'])

    def _create_game(self, **kw):
        try:
            home = self._resolve_team(kw['home'])
            away = self._resolve_team(kw['away'])
            dt = kw['datetime']
        except KeyError as e:
            raise ValueError(f"Missing required argument for game: {e.args[0]}")
        return Game(home, away, dt)

    def _create_cup(self, **kw):
        try:
            teams_raw = kw['teams']
        except KeyError:
            raise ValueError("Cup requires 'teams' argument")
        teams = [self._resolve_team(t) for t in teams_raw]
        type = kw.get('cup_type', None)
        rematch_enabled = type.endswith("2")
        interval = kw.get('interval', None)

        if (type not in ["ELIMINATION", "GROUP", "LEAGUE", "ELIMINATION2", "GROUP2", "LEAGUE2"]):
            raise ValueError("Invalid cup type")
        
        if type in ["ELIMINATION", "ELIMINATION2"]:
            cup = EliminationCup(teams, interval, rematch_enabled)

        elif type in ["GROUP", "GROUP2"]:
            cup = GroupCup(teams, interval, rematch_enabled)
            
        elif type in ["LEAGUE", "LEAGUE2"]:
            cup = LeagueCup(teams, interval, rematch_enabled)

        cup.watch(self)  # Catalog observes the cup for new games
        
        cup.initialize_games()  # Initialize the cup (e.g., schedule initial games)
        return cup

    def create(self, **kw):
        kind = kw.get('type', None)
        if not kind:
            raise ValueError("Missing 'type' ('team', 'game', or 'cup')")

        creators = {
            'team': self._create_team,
            'game': self._create_game,
            'cup': self._create_cup
        }

        if kind.lower() not in creators:
            raise ValueError(f"Unknown type: {kind}")

        obj = creators[kind.lower()](**kw)
        self.objectDict[obj.id()] = obj
        return obj.id()

    def list(self):
        return [(obj.id(), obj.description()) for obj in self.objectDict.values()]

    def listattached(self, user):
        if (user not in self.attachDict):
            raise ValueError()

        return [(objId, self.objectDict[objId].description()) for objId in self.attachDict[user]] 

    def attach(self, id, user):
        if user in self.attachDict:
            if id not in self.attachDict[user]:
                self.attachDict[user].append(id)
        else:
            self.attachDict[user] = [id]

    def detach(self, id, user):
        if user in self.attachDict:
            if id in self.attachDict[user]:
                self.attachDict[user].remove(id)
            else:
                raise ValueError()
        else:
            raise ValueError()

    def delete(self, id):
        if id not in self.objectDict:
            raise ValueError()
        
        isAttached = False

        for objIds in self.attachDict.values():
            if id in objIds:
                isAttached = True
                break
        
        if isAttached:
            raise ValueError()

        obj = self.objectDict.pop(id)
        
        #not sure if its necessary
        # del(obj)

    def update(self, event):
        if event["type"] == "new_game":
            game = event["game"]
            self.objectDict[game.id()] = game