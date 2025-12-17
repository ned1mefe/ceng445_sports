from flask import Blueprint, request, jsonify, abort
from api.shared import catalog
from api.utils import serialize_cup, parse_interval
from class_library.models.cup import Cup

cups_bp = Blueprint('cups', __name__)

@cups_bp.route('/', methods=['GET'])
def list_cups():
    cups = [serialize_cup(obj) for obj in catalog.objectDict.values() if isinstance(obj, Cup)]
    return jsonify(cups)

@cups_bp.route('/', methods=['POST'])
def create_cup():
    data = request.json
    # Expected: {"type": "LEAGUE", "teams": [id1, id2...], "interval_seconds": 60}
    try:
        interval = parse_interval(data.get('interval_seconds', 0))
        cup_id = catalog.create(
            type='cup',
            cup_type=data['type'],
            teams=data['teams'],
            interval=interval
        )
        return jsonify({"id": cup_id, "message": "Cup created"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@cups_bp.route('/<cid>', methods=['GET'])
def get_cup(cid):
    cup = catalog.objectDict.get(cid)
    if not cup or not isinstance(cup, Cup):
        abort(404)
    return jsonify(serialize_cup(cup))

@cups_bp.route('/<cid>', methods=['DELETE'])
def delete_cup(cid):
    try:
        catalog.delete(cid)
        return jsonify({"message": "Cup deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400