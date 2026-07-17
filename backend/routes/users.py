from flask import Blueprint, jsonify, request
from controllers.user_controller import analyze_selected_users, create_user, get_users

users_bp = Blueprint('users', __name__)


@users_bp.route('', methods=['GET'])
def list_users():
    return jsonify(get_users())


@users_bp.route('/analyze', methods=['POST'])
def analyze_users_route():
    data = request.get_json(silent=True) or {}
    user_ids = data.get("user_ids") or []
    if not isinstance(user_ids, list):
        user_ids = [user_ids] if user_ids else []
    return jsonify(analyze_selected_users(user_ids))


@users_bp.route('', methods=['POST'])
def create_user_route():
    data = request.get_json(silent=True) or {}
    return jsonify(create_user(data))
