from database.db import get_db
from models.user import User


def create_user(data):
    """Créer un nouvel utilisateur."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (nom, email, poste, departement, role) VALUES (?, ?, ?, ?, ?)",
        (
            data.get("nom", "Inconnu"),
            data.get("email", "unknown@example.com"),
            data.get("poste"),
            data.get("departement"),
            data.get("role", "user"),
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"id": user_id, "message": "user created"}


def get_users():
    """Récupérer tous les utilisateurs."""
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def analyze_selected_users(user_ids):
    """Analyse un sous-ensemble d’utilisateurs sélectionnés à partir de leurs tickets et de leur département."""
    if not user_ids:
        return {"message": "no users selected", "selected_users": []}

    conn = get_db()
    placeholders = ", ".join("?" for _ in user_ids)
    users = conn.execute(
        f"SELECT id, nom, departement, poste, role FROM users WHERE id IN ({placeholders}) ORDER BY id",
        user_ids,
    ).fetchall()
    tickets = conn.execute(
        "SELECT id, titre, categorie, departement_cible, statut, user_id FROM tickets WHERE user_id IN ({}) ORDER BY id DESC".format(placeholders),
        user_ids,
    ).fetchall()
    conn.close()

    selected_users = [dict(user) for user in users]
    related_tickets = [dict(ticket) for ticket in tickets]

    by_department = {}
    for user in selected_users:
        by_department[user["departement"]] = by_department.get(user["departement"], 0) + 1

    categories = {}
    for ticket in related_tickets:
        categories[ticket["categorie"]] = categories.get(ticket["categorie"], 0) + 1

    return {
        "message": "users analyzed",
        "selected_users": selected_users,
        "related_tickets": related_tickets,
        "summary": {
            "user_count": len(selected_users),
            "departments": by_department,
            "ticket_categories": categories,
            "open_tickets": sum(1 for t in related_tickets if t["statut"] == "ouvert"),
            "in_progress_tickets": sum(1 for t in related_tickets if t["statut"] == "en_cours"),
        },
    }
