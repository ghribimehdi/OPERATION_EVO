# Operation EVO

Projet Flask orienté backend-first pour la gestion de tickets, la supervision d’incidents et l’aide à la décision via IA.

## Objectif

Ce projet permet de :
- gérer des tickets de support / incidents
- affecter des tickets à des utilisateurs
- organiser les tickets dans des groupes de problèmes
- afficher des métriques de supervision temps réel
- proposer des analyses IA à partir de l’historique et des tickets similaires
- envoyer des emails de synthèse système

## Prérequis

- Python 3.10+
- Git
- Windows / PowerShell / CMD

## Démarrage rapide

### 1. Cloner le projet

```cmd
git clone <url-du-repo>
cd OPERATION_EVO
```

### 2. Créer et activer l’environnement virtuel

```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

### 3. Installer les dépendances

```cmd
pip install -r backend\requirements.txt
```

### 4. Lancer le backend

```cmd
cd backend
python app.py
```

Le projet sera accessible sur :
- http://127.0.0.1:5000/admin

### 5. Vérifier l’API

```cmd
curl http://127.0.0.1:5000/api/health
```

Résultat attendu :

```json
{"status": "ok"}
```

## Structure du projet

```text
OPERATION_EVO/
├── backend/
│   ├── app.py
│   ├── config.py
│   ├── controllers/
│   ├── database/
│   ├── models/
│   ├── routes/
│   ├── services/
│   ├── templates/
│   └── tests/
├── frontend/
└── README.md
```

## Fonctionnalités principales

- Gestion des tickets
- Affectation à un utilisateur
- Groupes de problèmes et synthèse par groupe
- Supervision temps réel avec métriques
- Historique d’activité et commentaires internes
- Suggestions IA via historique / tickets similaires
- Export CSV / JSON
- Envoi d’email de PR système

## Développement rapide

Pour commencer à travailler :
1. Activer le venv
2. Lancer `python app.py`
3. Ouvrir `http://127.0.0.1:5000/admin`
4. Modifier les fichiers dans `backend/`

## Notes importantes

- La base SQLite est initialisée automatiquement au démarrage.
- Le projet est actuellement orienté backend-first.
- Le dashboard admin se trouve dans `backend/templates/admin_dashboard.html`.

## Arrêter le serveur

Dans le terminal où le serveur tourne :

```cmd
Ctrl + C
```
