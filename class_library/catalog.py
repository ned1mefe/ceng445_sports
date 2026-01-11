import uuid
from class_library.models.cup import Cup
from class_library.models.cup_types.elimination_cup import EliminationCup
from class_library.models.cup_types.group_cup import GroupCup
from class_library.models.cup_types.league_cup import LeagueCup
from class_library.models.team import Team
from class_library.models.game import Game

class Catalog:
    def __init__(self):
        self.attachDict = {} # user (or userID) -> [objectId]
        self.objectDict = {} # objectId -> object
        self._broadcast_function = None  # Function to broadcast to all sessions
    
    def set_broadcast_function(self, func):
        """Register a function to broadcast notifications to all active sessions."""
        self._broadcast_function = func
    
    def _broadcast_to_all(self, event):
        """Broadcast an event to all active sessions."""
        if self._broadcast_function:
            self._broadcast_function(event)

    def _resolve_team(self, val):
        if val in self.objectDict:
            resolved = self.objectDict[val]
            if isinstance(resolved, Team):
                return resolved
            else:
                raise ValueError(f"Object with id {val} is not a Team")

        raise ValueError("Cannot resolve team: must be an active team id")

    def _create_team(self, **kw):
        team = Team(kw['name'], kw['year'], kw['country'])
        team.watch(self) 
        return team
    
    def _create_game(self, **kw):
        try:
            home = self._resolve_team(kw['home'])
            away = self._resolve_team(kw['away'])
            dt = kw['datetime']
        except KeyError as e:
            raise ValueError(f"Missing required argument for game: {e.args[0]}")
        game = Game(home, away, dt)
        game.watch(self)
        return game

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
        
        # Broadcast creation event to all sessions
        obj_type = kind.lower()
        event = {
            "type": f"{obj_type}_created",
            "id": obj.id(),
            "description": obj.description()
        }
        self._broadcast_to_all(event)
        
        return obj.id()

    def list(self):
        return [(obj.id(), obj.description()) for obj in self.objectDict.values()]

    def listattached(self, user):
        if (user not in self.attachDict):
            raise ValueError()

        return [(objId, self.objectDict[objId].description()) for objId in self.attachDict[user]] 

    def attach(self, id, user):
        self.objectDict[id].watch(user)

        if user in self.attachDict:
            if id not in self.attachDict[user]:
                self.attachDict[user].append(id)
        else:
            self.attachDict[user] = [id]

    def detach(self, id, user):
        self.objectDict[id].unwatch(user)

        if user in self.attachDict:
            if id in self.attachDict[user]:
                self.attachDict[user].remove(id)

        
    def detachAll(self, user):
        if user in self.attachDict:
            for objId in self.attachDict[user]:
                self.detach(objId, user)

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
        
        # Get object type for deletion event (before we modify obj)
        obj_type = obj.__class__.__name__.lower()
        if 'Cup' in obj_type:
            obj_type = 'cup'
        elif obj_type == 'game':
            obj_type = 'game'
        elif obj_type == 'team':
            obj_type = 'team'
        
        if isinstance(obj, Cup):
            for gid in list(obj._games.keys()):
                gameObj = obj._games.pop(gid)
                if gid in self.objectDict:
                    self.objectDict.pop(gid)

        if isinstance(obj, GroupCup):
            for letter, leagueCup in list(obj._groups.items()):
                for gid in list(leagueCup._games.keys()):
                    leagueCup._games.pop(gid)
                    if gid in self.objectDict:
                        self.objectDict.pop(gid)

                if leagueCup.id() in self.objectDict:
                    self.objectDict.pop(leagueCup.id())

            obj._groups.clear()

            # --- PLAYOFFS ---
            # obj._playOffs: EliminationCup object
            if obj._playOffs is not None:
                playoffsCup = obj._playOffs

                # playoffs içindeki tüm game'ler
                for gid in list(playoffsCup._games.keys()):
                    playoffsCup._games.pop(gid)
                    if gid in self.objectDict:
                        self.objectDict.pop(gid)

                # playoffs cup'ı da sil
                if playoffsCup.id() in self.objectDict:
                    self.objectDict.pop(playoffsCup.id())

                obj._playOffs = None
        
        # Broadcast deletion event to all sessions
        event = {
            "type": f"{obj_type}_deleted",
            "id": id
        }
        self._broadcast_to_all(event)

    def update(self, event):
        if event["type"] == "new_game":
            game = event["game"]
            self.objectDict[game.id()] = game
        
        if event["type"] == "new_group":
            group = event["group"]
            self.objectDict[group.id()] = group
        
        # Broadcast all events to all sessions (scores, game state changes, etc.)
        self._broadcast_to_all(event)


    def __getstate__(self):
        return {
            "objectDict": self.objectDict
        }


    def __setstate__(self, state):
        self.objectDict = state["objectDict"]
        self.attachDict = {}
        self._broadcast_function = None  # Will be set after unpickling

        self._restore_cup_observers()
    
    def _restore_cup_observers(self):
        for obj in self.objectDict.values():
            if str(obj)[-3:] == "Cup":
                obj.watch(self)