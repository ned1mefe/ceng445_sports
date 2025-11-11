from models.game import Game

class CupType():
    def __init__(self,cup, teams, rematch_enabled=False):
        self._cup = cup
        self._teams = teams
        self._games = {}  # gameId -> Game object
        self._rematch_enabled = rematch_enabled

        self._schedule_games()

    def teams(self):
        return self._teams
    
    def _create_game(self, team1, team2, datetime):
        game = Game(team1, team2, datetime)
        self._games[game.id()] = game

        game.watch(self._cup)  # Cup observes the game for events

        self._cup._notify({"type": "new_game", "game": game})  # Notify cup's observers
        return game
    

    def _schedule_games(self):
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def standings(self):
        raise NotImplementedError("This method should be implemented by subclasses")
    
    def gametree(self):
        raise NotImplementedError("This method should be implemented by subclasses")
    