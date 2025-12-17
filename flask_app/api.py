from flask import Flask, request, jsonify
from datetime import datetime

# Import your Phase 1 library
from catalog import Catalog
from models.team import Team
from models.game import Game
from models.cup import Cup

app = Flask(__name__)

# --- GLOBAL STATE ---
# Initialize the Catalog in memory. 
# In a REST API, this persists as long as the server script is running.
CATALOG = Catalog()

# --- HELPER FUNCTIONS ---
def success_response(value=None):
    """Encapsulates success results in the requested format."""
    return jsonify({"result": "success", "value": value}), 200

def error_response(reason, code=400):
    """Encapsulates error results."""
    return jsonify({"result": "error", "reason": reason}), code

# --- TEAM ROUTES ---

@app.route('/teams', methods=['GET', 'POST'])
def manage_teams():
    if request.method == 'GET':
        # List all teams
        teams = {}
        for obj_id, obj in CATALOG.objectDict.items():
            if isinstance(obj, Team):
                teams[obj_id] = obj.description()
        return success_response(teams)

    elif request.method == 'POST':
        # Create a new team
        data = request.get_json()
        if not data:
            return error_response("Missing JSON body")

        try:
            name = data.get('name')
            year = data.get('year')
            country = data.get('country')

            if not all([name, year, country]):
                return error_response("Missing fields: name, year, country")

            tid = CATALOG.create(type="team", name=name, year=year, country=country)
            return success_response({"id": tid, "message": "Team created"})
        except Exception as e:
            return error_response(str(e))

@app.route('/teams/<team_id>', methods=['GET', 'DELETE'])
def team_detail(team_id):
    if team_id not in CATALOG.objectDict:
        return error_response("Team not found", 404)

    team = CATALOG.objectDict[team_id]
    if not isinstance(team, Team):
        return error_response("ID exists but is not a Team")

    if request.method == 'GET':
        # Return full details
        return success_response({
            "id": team.id(),
            "name": team.name,
            "year": team.year,
            "country": team.country,
            "players": list(team.players.keys())
        })

    elif request.method == 'DELETE':
        try:
            CATALOG.delete(team_id)
            return success_response(f"Team {team_id} deleted")
        except Exception as e:
            return error_response(str(e))

# --- GAME ROUTES ---

@app.route('/games', methods=['GET', 'POST'])
def manage_games():
    if request.method == 'GET':
        games = {}
        for obj_id, obj in CATALOG.objectDict.items():
            if isinstance(obj, Game):
                games[obj_id] = obj.description()
        return success_response(games)

    elif request.method == 'POST':
        data = request.get_json()
        try:
            home_id = data.get('home')
            away_id = data.get('away')
            # Handle datetime parsing (JSON sends string)
            dt_str = data.get('datetime')
            dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M") if dt_str else datetime.now()

            gid = CATALOG.create(type="game", home=home_id, away=away_id, datetime=dt)
            return success_response({"id": gid, "message": "Game created"})
        except Exception as e:
            return error_response(str(e))

@app.route('/games/<game_id>', methods=['GET', 'PUT', 'DELETE'])
def game_detail(game_id):
    if game_id not in CATALOG.objectDict:
        return error_response("Game not found", 404)

    game = CATALOG.objectDict[game_id]
    if not isinstance(game, Game):
        return error_response("ID is not a Game")

    if request.method == 'GET':
        # Return current game stats
        return success_response(game.stats())

    elif request.method == 'PUT':
        # Handle state updates (Start, End, Score)
        data = request.get_json()
        action = data.get('action') # "start", "end", "score", "pause", "resume"

        try:
            if action == "start":
                game.start()
                return success_response("Game started")
            
            elif action == "end":
                game.end()
                return success_response("Game ended")
            
            elif action == "score":
                points = int(data.get('points', 0))
                team_id = data.get('team_id')
                player_name = data.get('player', None)

                # We must pass the Team object to game.score(), not the ID string
                if team_id not in CATALOG.objectDict:
                    return error_response("Invalid team ID provided for scoring")
                
                team_obj = CATALOG.objectDict[team_id]
                game.score(points, team_obj, player_name)
                return success_response("Score updated")
            
            elif action == "pause":
                 game.pause()
                 return success_response("Game paused")
            
            elif action == "resume":
                 game.resume()
                 return success_response("Game resumed")

            else:
                return error_response("Unknown action. Use start, end, score, pause, resume.")
        except Exception as e:
            return error_response(str(e))

    elif request.method == 'DELETE':
        try:
            CATALOG.delete(game_id)
            return success_response(f"Game {game_id} deleted")
        except Exception as e:
            return error_response(str(e))

# --- CUP ROUTES ---

@app.route('/cups', methods=['GET', 'POST'])
def manage_cups():
    if request.method == 'GET':
        cups = {}
        for obj_id, obj in CATALOG.objectDict.items():
            # Check if it is a Cup instance
            if "Cup" in obj.__class__.__name__:
                cups[obj_id] = obj.description()
        return success_response(cups)

    elif request.method == 'POST':
        data = request.get_json()
        try:
            cup_type = data.get('cup_type') # ELIMINATION, LEAGUE, GROUP
            teams = data.get('teams', [])
            interval = int(data.get('interval', 1))

            cid = CATALOG.create(type="cup", cup_type=cup_type, teams=teams, interval=interval)
            return success_response({"id": cid, "message": f"{cup_type} created"})
        except Exception as e:
            return error_response(str(e))

@app.route('/cups/<cup_id>', methods=['GET', 'DELETE'])
def cup_detail(cup_id):
    if cup_id not in CATALOG.objectDict:
        return error_response("Cup not found", 404)

    cup = CATALOG.objectDict[cup_id]

    if request.method == 'GET':
        return success_response(cup.standings())

    elif request.method == 'DELETE':
        try:
            CATALOG.delete(cup_id)
            return success_response(f"Cup {cup_id} deleted")
        except Exception as e:
            return error_response(str(e))

if __name__ == '__main__':
    # Run the server on port 5000
    app.run(debug=True, port=5000)