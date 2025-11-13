import uuid
import time 

class Game():
    def __init__(self, home, away, datetime):
        self._home_team = home
        self._away_team = away
        self._datetime = datetime
        self._id = str(uuid.uuid4())

        home.games.append(self)
        away.games.append(self)
        for observer in home.observers:
            self.watch(observer)
        for observer in away.observers:
            self.watch(observer)
        
        self.is_running = False
        self.is_ended = False
        self.observers = set()
        self.timeline = []

        self._stats = {"Home": {"score": 0},
                      "Away": {"score": 0}}

        try:
            for player_name in home.players:
                    self._stats["Home"][player_name] = 0
        except AttributeError:
            print(f"Team {home.name} does not contain players")
            
        try:
            for player_name in away.players:
                    self._stats["Away"][player_name] = 0
        except AttributeError:
            print(f"Team {away.name} does not contain players")

    def id(self):
        return self._id
    
    def home(self):
        return self._home_team
    
    def away(self):
        return self._away_team
    
    def start(self):
        if self.is_running:
            raise ValueError("Game already started")
        if self.is_ended:
            raise ValueError("Game has already ended")
        
        self.is_running = True
        self._notify({"type": "game_started", "game": self})

    def pause(self):
        if not self.is_running:
            raise ValueError("Game is not running")
        
        self.is_running = False
        self._notify({"type": "game_paused", "game": self})

    def resume(self):
        if self.is_running:
            raise ValueError("Game already running")
        if self.is_ended:
            raise ValueError("Game has already ended")
        
        self.is_running = True
        self._notify({"type": "game_resumed", "game": self})

    def end(self):
        if self.is_ended:
            raise ValueError("Game has already ended")

        self.is_running = False
        self.is_ended = True 
        self._notify({"type": "game_ended", "game": self})
    
    def score(self, points, team, player = None):
        if team.name == self._home_team.name:
            team_key = "Home"
        elif team.name == self._away_team.name:
            team_key = "Away"
        else:
            raise ValueError("Team not in game")
            
        if (player) and player not in self._stats[team_key]:
            raise ValueError(f"Player '{player}' not on {team_key} roster")
       
        self._stats[team_key]["score"] += points
        if player:
            self._stats[team_key][player] += points 
        
        game_time_str = "00:00.0" # placeholder
        self.timeline.append( (game_time_str, team_key, player, points) ) 

        self._notify({"type": "score", "game": self, "team": team, "player": player, "points": points})

    # --- Observer Methods ---
    def watch(self, obj):
        if obj:
            self.observers.add(obj)
   
    def unwatch(self, obj):
        self.observers.discard(obj)


    def _notify(self, event):
        for obs in self.observers:
            obs.update(event)

    def stats(self):
        home_player_stats = {
            player: score for player, score in self._stats["Home"].items()
            if player != "score"
        }
        away_player_stats = {
            player: score for player, score in self._stats["Away"].items()
            if player != "score"
        }

        if self.is_ended:
            game_time_str = "Full Time"
        else:
            game_time_str = "00:00.0" # Placeholder

        return {
            "Home": {
                "Name": self._home_team.name,
                "Pts": self._stats["Home"]["score"], 
                "Players": home_player_stats       
            },
            "Away": {
                "Name": self._away_team.name,
                "Pts": self._stats["Away"]["score"],
                "Players": away_player_stats       
            },
            "Time": game_time_str,
            "Timeline": self.timeline
        }
        
    def __str__(self):
        return f"Game: {self._home_team.name} vs {self._away_team.name}"
    
    def description(self):
        return str(self)