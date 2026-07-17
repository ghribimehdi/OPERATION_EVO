import csv
import io
import json
from datetime import datetime

from database.db import get_db
from services.email_service import send_ticket_notification
from services.mistral_service import classify_ticket
from services.similarity_service import build_ai_suggestions


def _now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _record_activity(conn, ticket_id, action, details=None):
    conn.execute(
        "INSERT INTO ticket_activity (ticket_id, action, details, created_at) VALUES (?, ?, ?, ?)",
        (ticket_id, action, json.dumps(details or {}, ensure_ascii=False), _now()),
    )


def assign_ticket_to_user(ticket_id, user_id, group_id=None):
    """Affecter un ticket à un utilisateur spécifique, en respectant le groupe de problème si fourni."""
    conn = get_db()
    cursor = conn.cursor()
    if group_id is not None:
        cursor.execute("SELECT id FROM tickets WHERE id = ? AND groupe_id = ?", (ticket_id, group_id))
        existing = cursor.fetchone()
        if existing is None:
            conn.close()
            return {"error": "ticket not found in selected problem group"}, 400
    cursor.execute("UPDATE tickets SET user_id = ? WHERE id = ?", (user_id, ticket_id))
    cursor.execute(
        "INSERT INTO ticket_history (ticket_id, action, date_action) VALUES (?, ?, ?)",
        (ticket_id, "assigned", _now()),
    )
    _record_activity(conn, ticket_id, "assigned", {"user_id": user_id, "group_id": group_id})
    conn.commit()
    conn.close()
    return {"id": ticket_id, "user_id": user_id, "group_id": group_id, "message": "ticket assigned"}


def analyze_ticket(data):
    """Retourne une analyse IA complète à partir d'un ticket fictif."""
    classification = classify_ticket(data.get("description", "") or data.get("titre", ""))
    suggestions = build_ai_suggestions(data)
    return {
        "message": "analysis ready",
        "classification": classification,
        "ai_suggestions": suggestions,
    }


def create_ticket(data):
    """Créer un nouveau ticket avec classification IA et suggestions de résolution."""
    analysis = analyze_ticket(data)
    classification = analysis.get("classification", {})
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO tickets (titre, description, categorie, gravite, priorite, departement_cible, statut, user_id, groupe_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("titre", "Sans titre"),
            data.get("description", ""),
            classification.get("categorie", "autre"),
            classification.get("gravite", "moyenne"),
            classification.get("priorite", "normal"),
            classification.get("departement", "support"),
            data.get("statut", "ouvert"),
            data.get("user_id"),
            data.get("groupe_id"),
        ),
    )
    ticket_id = cursor.lastrowid
    cursor.execute(
        "INSERT INTO ticket_history (ticket_id, action, date_action) VALUES (?, ?, ?)",
        (ticket_id, "created", _now()),
    )
    _record_activity(conn, ticket_id, "ticket_created", {"source": "api"})
    conn.commit()
    conn.close()
    return {
        "id": ticket_id,
        "message": "ticket created",
        "classification": classification,
        "ai_suggestions": analysis.get("ai_suggestions"),
    }


def get_tickets(filters=None):
    """Récupérer tous les tickets avec filtres optionnels."""
    filters = filters or {}
    conn = get_db()
    query = "SELECT * FROM tickets"
    clauses = []
    params = []
    if filters.get("statut"):
        clauses.append("statut = ?")
        params.append(filters["statut"])
    if filters.get("priorite"):
        clauses.append("priorite = ?")
        params.append(filters["priorite"])
    if filters.get("departement"):
        clauses.append("departement_cible = ?")
        params.append(filters["departement"])
    if filters.get("user_id"):
        clauses.append("user_id = ?")
        params.append(filters["user_id"])
    if filters.get("groupe_id"):
        clauses.append("groupe_id = ?")
        params.append(filters["groupe_id"])
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_ticket_by_id(ticket_id):
    """Récupérer un ticket par son identifiant."""
    conn = get_db()
    row = conn.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    conn.close()
    return None if row is None else dict(row)


def get_history_tickets():
    """Récupérer les tickets déjà reçus ou traités pour l'historique."""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT t.*, u.nom AS user_nom, u.email AS user_email
        FROM tickets t
        LEFT JOIN users u ON u.id = t.user_id
        WHERE COALESCE(t.statut, '') IN ('resolu', 'résolu', 'traité', 'traitée', 'reçu', 'recu', 'en_cours', 'ouvert')
        ORDER BY t.id DESC
        """
    ).fetchall()
    conn.close()
    tickets = [dict(row) for row in rows]
    for ticket in tickets:
        status = str(ticket.get("statut") or "").strip().lower()
        if status in {"resolu", "résolu", "traité", "traitée", "traitée", "traite", "traitee"}:
            ticket["historique_type"] = "traité"
        elif status in {"reçu", "recu", "reçue", "recue"}:
            ticket["historique_type"] = "reçu"
        else:
            ticket["historique_type"] = "reçu"
    return tickets


def delete_ticket(ticket_id):
    """Supprimer un ticket de l'historique."""
    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if existing is None:
        conn.close()
        return {"error": "ticket not found"}
    cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
    conn.commit()
    conn.close()
    return {"id": ticket_id, "message": "ticket deleted"}


def update_ticket_status(ticket_id, new_status=None, assigned_user_id=None, priority=None, metadata=None):
    """Mettre à jour le statut d'un ticket, son assignation et sa priorité."""
    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT id, statut, user_id, priorite FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if existing is None:
        conn.close()
        return {"error": "ticket not found"}, 404

    updates = {}
    if new_status is not None:
        updates["statut"] = new_status
    if priority is not None:
        updates["priorite"] = priority
    if assigned_user_id is not None:
        updates["user_id"] = assigned_user_id

    if updates:
        fields = ", ".join(f"{field} = ?" for field in updates.keys())
        cursor.execute(f"UPDATE tickets SET {fields} WHERE id = ?", list(updates.values()) + [ticket_id])

    if new_status is not None and new_status != existing["statut"]:
        cursor.execute(
            "INSERT INTO ticket_history (ticket_id, action, date_action) VALUES (?, ?, ?)",
            (ticket_id, "status_changed", _now()),
        )
        _record_activity(conn, ticket_id, "status_changed", {"status": new_status, "metadata": metadata or {}})

    if assigned_user_id is not None and assigned_user_id != existing["user_id"]:
        cursor.execute(
            "INSERT INTO ticket_history (ticket_id, action, date_action) VALUES (?, ?, ?)",
            (ticket_id, "assigned", _now()),
        )
        _record_activity(conn, ticket_id, "assigned", {"user_id": assigned_user_id})

    if priority is not None and priority != existing["priorite"]:
        _record_activity(conn, ticket_id, "priority_changed", {"priority": priority})

    conn.commit()
    conn.close()
    return {
        "id": ticket_id,
        "statut": new_status or existing["statut"],
        "user_id": assigned_user_id or existing["user_id"],
        "priorite": priority or existing["priorite"],
        "message": "status updated",
    }


def create_ticket_comment(ticket_id, user_id, text):
    """Ajouter un commentaire interne sur un ticket."""
    if not text or not str(text).strip():
        return {"error": "comment text is required"}, 400
    conn = get_db()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT id FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if existing is None:
        conn.close()
        return {"error": "ticket not found"}, 404
    cursor.execute(
        "INSERT INTO ticket_comments (ticket_id, user_id, message, date_creation) VALUES (?, ?, ?, ?)",
        (ticket_id, user_id, text.strip(), _now()),
    )
    cursor.execute(
        "INSERT INTO ticket_history (ticket_id, action, date_action) VALUES (?, ?, ?)",
        (ticket_id, "comment_added", _now()),
    )
    _record_activity(conn, ticket_id, "comment_added", {"message": text.strip()})
    conn.commit()
    conn.close()
    return {"id": cursor.lastrowid, "ticket_id": ticket_id, "message": text.strip(), "user_id": user_id}


def get_ticket_comments(ticket_id):
    """Récupérer les commentaires d’un ticket."""
    conn = get_db()
    rows = conn.execute(
        """
        SELECT c.id, c.ticket_id, c.user_id, c.message, c.date_creation, u.nom AS user_name
        FROM ticket_comments c
        LEFT JOIN users u ON u.id = c.user_id
        WHERE c.ticket_id = ?
        ORDER BY c.id ASC
        """,
        (ticket_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_ticket_activity(ticket_id):
    """Récupérer l’historique d’activité d’un ticket."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, ticket_id, action, details, created_at FROM ticket_activity WHERE ticket_id = ? ORDER BY id ASC",
        (ticket_id,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def export_tickets(format="csv"):
    """Exporter les tickets en CSV ou JSON."""
    conn = get_db()
    rows = conn.execute(
        "SELECT id, titre, description, categorie, gravite, priorite, departement_cible, statut, date_creation, user_id, groupe_id FROM tickets ORDER BY id DESC"
    ).fetchall()
    conn.close()
    payload = [dict(row) for row in rows]
    if str(format).lower() == "json":
        return json.dumps(payload, ensure_ascii=False, indent=2)
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "titre", "statut", "priorite", "departement_cible", "date_creation"],
    )
    writer.writeheader()
    for row in payload:
        writer.writerow({
            "id": row.get("id"),
            "titre": row.get("titre"),
            "statut": row.get("statut"),
            "priorite": row.get("priorite"),
            "departement_cible": row.get("departement_cible"),
            "date_creation": row.get("date_creation"),
        })
    return output.getvalue()


def get_ticket_metrics():
    """Retourne un résumé rapide des tickets par statut et priorité."""
    conn = get_db()
    rows = conn.execute(
        "SELECT statut, priorite, COUNT(*) as count FROM tickets GROUP BY statut, priorite ORDER BY statut, priorite"
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_ticket_metrics_summary():
    """Retourne un résumé synthétique, utilisable directement par le dashboard."""
    metrics = get_ticket_metrics()
    by_status = {}
    by_priority = {}
    for metric in metrics:
        status = str(metric.get("statut") or "inconnu")
        priority = str(metric.get("priorite") or "inconnu")
        by_status[status] = by_status.get(status, 0) + int(metric.get("count") or 0)
        by_priority[priority] = by_priority.get(priority, 0) + int(metric.get("count") or 0)
    return {
        "total_tickets": sum(by_status.values()),
        "by_status": by_status,
        "by_priority": by_priority,
        "rows": metrics,
    }
