import json
import os
import requests
from config import Config


def classify_ticket(description):
    """Classe un ticket à partir de mots-clés simples et d'une éventuelle API Mistral si configurée."""
    api_key = Config.MISTRAL_API_KEY
    if api_key and api_key != "à_remplacer":
        try:
            response = requests.post(
                "https://api.mistral.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "mistral-small-latest",
                    "messages": [
                        {"role": "system", "content": "Tu classifies des tickets support. Réponds uniquement en JSON avec categorie, gravite, priorite, departement."},
                        {"role": "user", "content": description or ""},
                    ],
                },
                timeout=10,
            )
            if response.ok:
                payload = response.json()
                content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
                if content:
                    try:
                        content = content.strip()
                        if content.startswith("```"):
                            content = content.strip("`\n")
                        parsed = json.loads(content)
                        if isinstance(parsed, dict):
                            return {
                                "categorie": parsed.get("categorie", "support"),
                                "gravite": parsed.get("gravite", "moyenne"),
                                "priorite": parsed.get("priorite", "normal"),
                                "departement": parsed.get("departement", "support"),
                            }
                    except Exception:
                        pass
        except Exception:
            pass

    lower = (description or "").lower()

    if any(word in lower for word in ["connexion", "sso", "login", "auth", "mot de passe", "session", "token", "acces", "access", "se connecter", "connexion bloquée", "connecter", "connecte", "connecté"]):
        categorie = "access"
        departement = "IT"
    elif any(word in lower for word in ["facture", "paiement", "finance", "bulletin", "salaire", "compta"]):
        categorie = "facturation"
        departement = "Finance"
    elif any(word in lower for word in ["rh", "contrat", "ressource humaine", "recrutement", "paie"]):
        categorie = "rh"
        departement = "RH"
    elif any(word in lower for word in ["achat", "commande", "livraison", "fournisseur", "stock"]):
        categorie = "achats"
        departement = "Achats"
    elif any(word in lower for word in ["bug", "erreur", "incident", "plantage", "affichage", "rapport", "interface"]):
        categorie = "bug"
        departement = "Produit"
    else:
        categorie = "autre"
        departement = "support"

    if any(word in lower for word in ["bloquant", "critique", "outage", "impossible", "ne plus"]):
        gravite = "haute"
    elif any(word in lower for word in ["urgent", "important", "prioritaire"]):
        gravite = "moyenne"
    else:
        gravite = "faible"

    if gravite == "haute":
        priorite = "urgent"
    elif gravite == "moyenne":
        priorite = "normal"
    else:
        priorite = "faible"

    return {
        "categorie": categorie,
        "gravite": gravite,
        "priorite": priorite,
        "departement": departement,
    }
