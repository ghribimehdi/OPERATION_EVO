from flask import Blueprint, jsonify
from controllers.stats_controller import get_dashboard_stats, get_periodic_summary

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('', methods=['GET'])
def dashboard_stats():
    return jsonify(get_dashboard_stats())


@stats_bp.route('/periodic', methods=['GET'])
def periodic_summary():
    period = 'month'
    return jsonify(get_periodic_summary(period))
