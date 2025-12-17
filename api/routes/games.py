from flask import Blueprint, request, jsonify, abort
from datetime import datetime
from api.shared import catalog
from api.utils import serialize_game
from class_library.models.game import Game

games_bp = Blueprint('games', __name__)

@games_bp.route('/', methods=['POST'])
def create_game():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Missing JSON body"}), 400

    try:
        home_id = data.get('home')
        away_id = data.get('away')
        dt_str = data.get('datetime') # Expected format: "YYYY-MM-DD HH:MM"

        if not home_id or not away_id:
            return jsonify({"error": "Missing 'home' or 'away' team IDs"}), 400

        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M") if dt_str else datetime.now()

        gid = catalog.create(type="game", home=home_id, away=away_id, datetime=dt)
        
        return jsonify({"message": "Game created", "id": gid}), 201

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal server error: " + str(e)}), 500
    


@games_bp.route('/', methods=['GET'])
def list_games():
    games = [serialize_game(obj) for obj in catalog.objectDict.values() if isinstance(obj, Game)]
    return jsonify(games)

@games_bp.route('/<gid>', methods=['GET'])
def get_game(gid):
    game = catalog.objectDict.get(gid)
    if not game or not isinstance(game, Game):
        abort(404)
    return jsonify(serialize_game(game))

@games_bp.route('/<gid>/stats', methods=['GET'])
def get_game_stats(gid):
    """
    Dedicated endpoint to retrieve only the stats of a specific game.
    """
    game = catalog.objectDict.get(gid)
    if not game or not isinstance(game, Game):
        abort(404)
    return jsonify(game.stats())


@games_bp.route('/<gid>/status', methods=['PUT'])
def update_status(gid):
    game = catalog.objectDict.get(gid)
    if not game or not isinstance(game, Game):
        abort(404)
    
    data = request.json
    action = data.get('action')
    
    try:
        if action == 'start':
            game.start()
        elif action == 'pause':
            game.pause()
        elif action == 'resume':
            game.resume()
        elif action == 'end':
            game.end()
        else:
            return jsonify({"error": "Invalid action"}), 400
        return jsonify({"message": f"Game {action}ed", "stats": game.stats()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@games_bp.route('/<gid>/score', methods=['PUT'])
def add_score(gid):
    game = catalog.objectDict.get(gid)
    if not game or not isinstance(game, Game):
        abort(404)
    
    data = request.json
    # Expected: {"team_side": "home" or "away", "points": 1, "player": "Name"}
    
    try:
        side = data.get('team_side', '').lower()
        if side == 'home':
            team_obj = game.home()
        elif side == 'away':
            team_obj = game.away()
        else:
            return jsonify({"error": "Invalid team_side (use 'home' or 'away')"}), 400
            
        points = int(data.get('points', 1))
        player_name = data.get('player', None)
        
        game.score(points, team_obj, player_name)
        return jsonify({"message": "Score updated", "stats": game.stats()})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@games_bp.route('/<gid>', methods=['DELETE'])
def delete_game(gid):
    try:
        catalog.delete(gid)
        return jsonify({"message": "Game deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400