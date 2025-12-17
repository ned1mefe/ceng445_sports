from flask import Blueprint, request, jsonify, abort
from api.shared import catalog
from api.utils import serialize_team
from class_library.models.team import Team

teams_bp = Blueprint('teams', __name__)

@teams_bp.route('/', methods=['GET'])
def list_teams():
    teams = [serialize_team(obj) for obj in catalog.objectDict.values() if isinstance(obj, Team)]
    return jsonify(teams)

@teams_bp.route('/', methods=['POST'])
def create_team():
    data = request.json
    try:
        tid = catalog.create(type='team', name=data['name'], year=data.get('year'), country=data.get('country'))
        return jsonify({"id": tid, "message": "Team created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@teams_bp.route('/<tid>', methods=['GET'])
def get_team(tid):
    team = catalog.objectDict.get(tid)
    if not team or not isinstance(team, Team):
        abort(404, description="Team not found")
    return jsonify(serialize_team(team))

@teams_bp.route('/<tid>', methods=['DELETE'])
def delete_team(tid):
    try:
        catalog.delete(tid)
        return jsonify({"message": "Team deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@teams_bp.route('/<tid>/players', methods=['POST'])
def add_player(tid):
    team = catalog.objectDict.get(tid)
    if not team or not isinstance(team, Team):
        abort(404)
    
    data = request.json
    try:
        team.addplayer(data['name'], data['number'])
        return jsonify({"message": f"Player {data['name']} added"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@teams_bp.route('/<tid>/players/<name>', methods=['DELETE'])
def remove_player(tid, name):
    team = catalog.objectDict.get(tid)
    if not team or not isinstance(team, Team):
        abort(404)
    
    try:
        team.delplayer(name)
        return jsonify({"message": f"Player {name} deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400