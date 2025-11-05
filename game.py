import uuid
import time 

class Game():
    def __init__(self, home, away, datetime):
        self._home_team = home
        self._away_team = away
        self._datetime = datetime
        self._id = uuid.uuid4()
        
        self.is_running = False
        self.is_ended = False
        self.observers = []
        self.timeline = []

        self._stats = {"Home": {"score": 0},
                      "Away": {"score": 0}}

        try:
            for player_name in home.players:
                    self._stats["Home"][player_name] = 0
        except AttributeError:
            print(f"Warning: Team {home.name} has no 'players' attribute.")
            
        try:
            for player_name in away.players:
                    self._stats["Away"][player_name] = 0
        except AttributeError:
            print(f"Warning: Team {away.name} has no 'players' attribute.")

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
        # self._notify_observers()

    def pause(self):
        if not self.is_running:
            raise ValueError("Game is not running")
        
        self.is_running = False
        # self._notify_observers()

    def resume(self):
        if self.is_running:
            raise ValueError("Game already running")
        if self.is_ended:
            raise ValueError("Game has already ended")
        
        self.is_running = True
        # self._notify_observers()

    def end(self):
        if self.is_ended:
            raise ValueError("Game has already ended")

        self.is_running = False
        self.is_ended = True 
        # self._notify_observers()
    
    def score(self, points, team, player):
        if team.name == self._home_team.name:
            team_key = "Home"
        elif team.name == self._away_team.name:
            team_key = "Away"
        else:
            raise ValueError("Team not in game")
            
        if player not in self._stats[team_key]:
            raise ValueError(f"Player '{player}' not on {team_key} roster")
       
        self._stats[team_key]["score"] += points
        self._stats[team_key][player] += points
        
        game_time_str = "00:00.0" # placeholder
        self.timeline.append( (game_time_str, team_key, player, points) )
        
        # self._notify_observers()

    # --- Observer Methods ---
    def watch(self, obj):
        if obj not in self.observers:
            self.observers.append(obj)
   
    def unwatch(self, obj):
        try:
            self.observers.remove(obj)
        except ValueError:
            pass

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