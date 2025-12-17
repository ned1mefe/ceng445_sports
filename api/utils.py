from datetime import timedelta
from flask import jsonify

def parse_interval(seconds):
    """Converts seconds integer to timedelta."""
    return timedelta(seconds=int(seconds))

def serialize_team(team):
    return {
        "id": team.id(),
        "name": team.name,
        "country": team.country,
        "year": team.year,
        "players": {name: p.number for name, p in team.numbers.items() if p} 
    }

def serialize_game(game):
    return {
        "id": game.id(),
        "home": game.home().name,
        "away": game.away().name,
        "date": str(game._datetime),
        "status": "Ended" if game.is_ended else "Running" if game.is_running else "Scheduled",
        "stats": game.stats()
    }

def serialize_cup(cup):
    return {
        "id": cup.id(),
        "description": str(cup),
        "standings": cup.standings()
    }