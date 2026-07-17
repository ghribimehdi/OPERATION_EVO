from flask import Blueprint, jsonify, request, Response
from controllers.ticket_controller import (
    analyze_ticket,
    assign_ticket_to_user,
    create_ticket,
    create_ticket_comment,
    delete_ticket,
    export_tickets,
    get_history_tickets,
    get_ticket_activity,
    get_ticket_by_id,
    get_ticket_comments,
    get_ticket_metrics,
    get_ticket_metrics_summary,
    get_tickets,
    update_ticket_status,
)
from services.similarity_service import get_problem_updates, group_problem_tickets, suggest_group_assignment

tickets_bp = Blueprint('tickets', __name__)


@tickets_bp.route('', methods=['GET'])
def list_tickets():
    filters = {}
    for key in ("statut", "priorite", "departement", "user_id", "groupe_id"):
        value = request.args.get(key)
        if value not in (None, ""):
            filters[key] = value
    return jsonify(get_tickets(filters=filters))


@tickets_bp.route('/metrics', methods=['GET'])
def ticket_metrics_route():
    return jsonify(get_ticket_metrics())


@tickets_bp.route('/metrics-summary', methods=['GET'])
def ticket_metrics_summary_route():
    return jsonify(get_ticket_metrics_summary())


@tickets_bp.route('/ai-analysis', methods=['POST'])
def ai_analysis_route():
    data = request.get_json(silent=True) or {}
    return jsonify(analyze_ticket(data))


@tickets_bp.route('/problem-groups', methods=['GET'])
def problem_groups_route():
    return jsonify(group_problem_tickets())


@tickets_bp.route('/problem-updates', methods=['GET'])
def problem_updates_route():
    problem_group_id = request.args.get('group_id', type=int)
    return jsonify(get_problem_updates(problem_group_id))


@tickets_bp.route('/problem-groups/<int:group_id>/suggest-assignee', methods=['GET', 'POST'])
def problem_group_suggest_assignee_route(group_id):
    result = suggest_group_assignment(group_id)
    if isinstance(result, tuple) and len(result) == 2 and result[1] >= 400:
        return jsonify(result[0]), result[1]
    return jsonify(result)


@tickets_bp.route('/history', methods=['GET'])
def history_tickets_route():
    return jsonify(get_history_tickets())


@tickets_bp.route('/export', methods=['GET'])
def export_tickets_route():
    fmt = request.args.get('format', 'csv').lower()
    payload = export_tickets(format=fmt)
    if fmt == 'json':
        return jsonify({'format': fmt, 'data': payload})
    return Response(payload, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=tickets.csv'})


@tickets_bp.route('', methods=['POST'])
def create_ticket_route():
    data = request.get_json(silent=True) or {}
    return jsonify(create_ticket(data))


@tickets_bp.route('/<int:ticket_id>', methods=['GET'])
def get_ticket_route(ticket_id):
    ticket = get_ticket_by_id(ticket_id)
    if ticket is None:
        return jsonify({"error": "ticket not found"}), 404
    return jsonify(ticket)


@tickets_bp.route('/<int:ticket_id>', methods=['PUT'])
def update_ticket_status_route(ticket_id):
    data = request.get_json(silent=True) or {}
    new_status = data.get('statut') or data.get('status')
    assigned_user_id = data.get('assigned_user_id') or data.get('user_id')
    priority = data.get('priority') or data.get('priorite')
    metadata = data.get('metadata', {})
    return jsonify(update_ticket_status(ticket_id, new_status=new_status, assigned_user_id=assigned_user_id, priority=priority, metadata=metadata))


@tickets_bp.route('/<int:ticket_id>', methods=['DELETE'])
def delete_ticket_route(ticket_id):
    result = delete_ticket(ticket_id)
    if result.get('error'):
        return jsonify(result), 404
    return jsonify(result)


@tickets_bp.route('/<int:ticket_id>/assign', methods=['POST'])
def assign_ticket_route(ticket_id):
    data = request.get_json(silent=True) or {}
    user_id = data.get('user_id')
    group_id = data.get('group_id')
    if user_id in (None, ''):
        return jsonify({"error": "user_id is required"}), 400
    return jsonify(assign_ticket_to_user(ticket_id, user_id, group_id=group_id))


@tickets_bp.route('/<int:ticket_id>/comments', methods=['GET'])
def list_ticket_comments_route(ticket_id):
    return jsonify(get_ticket_comments(ticket_id))


@tickets_bp.route('/<int:ticket_id>/comments', methods=['POST'])
def create_ticket_comment_route(ticket_id):
    data = request.get_json(silent=True) or {}
    result = create_ticket_comment(ticket_id, data.get('user_id'), data.get('message') or data.get('text'))
    if isinstance(result, tuple) and result[1] >= 400:
        return jsonify(result[0]), result[1]
    return jsonify(result)


@tickets_bp.route('/<int:ticket_id>/activity', methods=['GET'])
def ticket_activity_route(ticket_id):
    return jsonify(get_ticket_activity(ticket_id))
