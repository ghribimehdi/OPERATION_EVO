import os
import sqlite3
import sys
import threading
import time
from pathlib import Path
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_cors import CORS

BACKEND_ROOT = Path(__file__).resolve().parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from routes import users_bp, tickets_bp, stats_bp
from database.db import init_db, get_db
from config import Config
from services.email_service import send_weekly_system_email


app = Flask(__name__, template_folder='templates')
app.config.from_object(Config)
CORS(app)

app.register_blueprint(users_bp, url_prefix='/api/users')
app.register_blueprint(tickets_bp, url_prefix='/api/tickets')
app.register_blueprint(stats_bp, url_prefix='/api/stats')


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({"status": "ok"})


@app.route('/admin', methods=['GET'])
def admin_dashboard():
    return render_template('admin_dashboard.html', history_pin=Config.HISTORY_PIN)


@app.route('/images.png')
def serve_dashboard_image():
    return send_from_directory(app.template_folder, 'images.png', mimetype='image/png')


@app.route('/api/system-email/weekly', methods=['POST'])
def trigger_weekly_email():
    payload = request.get_json(silent=True) or {}
    recipient = payload.get('recipient')
    result = send_weekly_system_email(recipient=recipient)
    return jsonify(result)


def weekly_email_worker():
    while True:
        time.sleep(604800)
        send_weekly_system_email()


init_db(force=False)

if not os.getenv('FLASK_ENV') == 'test':
    thread = threading.Thread(target=weekly_email_worker, daemon=True)
    thread.start()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
