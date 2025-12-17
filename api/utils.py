from datetime import timedelta
from flask import jsonify

def parse_interval(days):
    """Converts days integer to timedelta."""
    return timedelta(days=int(days))

def serialize_team(team):
    return {
        "id": team.id(),
        "name": team.name,
        "country": team.country,
        "year": team.year,
        "players": {name: p._name for name, p in team.numbers.items() if p} 
    }

def serialize_game(game):
    return {
        "id": game.id(),
        "home": game.home().name,
        "away": game.away().name,
        "date": str(game._datetime),
        "status": "Ended" if game.is_ended else "Running" if game.is_running else "Scheduled"
    }

def serialize_cup(cup):
    return {
        "id": cup.id(),
        "description": str(cup),
        "games": [serialize_game(g) for g in cup._games.values()]
    }