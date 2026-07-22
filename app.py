from flask import Flask, render_template, request, jsonify, send_file, make_response
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import sqlite3
import json
import os
import base64
import jwt
from io import BytesIO
import csv
from functools import wraps

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['ADMIN_PASSWORD_HASH'] = generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads')
app.config['DATABASE'] = os.environ.get('DATABASE', 'fueltrack.db')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS vehicles (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            plate TEXT,
            fuel_type TEXT,
            color TEXT,
            created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS fills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id TEXT NOT NULL,
            date TEXT NOT NULL,
            volume REAL NOT NULL,
            price_per_liter REAL NOT NULL,
            total REAL NOT NULL,
            km INTEGER,
            lat REAL,
            lng REAL,
            photo TEXT,
            created_at TEXT,
            FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
        );
    """)
    conn.commit()
    conn.close()

# ========== AUTHENTICATION ==========
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        if not token:
            return jsonify({'message': 'Token manquant'}), 401
        try:
            jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Token invalide'}), 401
        return f(*args, **kwargs)
    return decorated

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    password = data.get('password', '')
    if check_password_hash(app.config['ADMIN_PASSWORD_HASH'], password):
        token = jwt.encode(
            {'exp': datetime.utcnow() + timedelta(days=30), 'iat': datetime.utcnow()},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({'success': True, 'token': token})
    return jsonify({'success': False, 'message': 'Mot de passe incorrect'}), 401

@app.route('/api/auth/check', methods=['GET'])
def check_auth():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({'authenticated': False})
    try:
        jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return jsonify({'authenticated': True})
    except:
        return jsonify({'authenticated': False})

# ========== PUBLIC ROUTES (Login page) ==========
@app.route('/')
def index():
    return render_template('index.html')

# ========== PROTECTED API ROUTES ==========
@app.route('/api/vehicles', methods=['GET'])
@token_required
def get_vehicles():
    conn = get_db()
    vehicles = conn.execute('SELECT * FROM vehicles ORDER BY created_at DESC').fetchall()
    conn.close()
    return jsonify([dict(v) for v in vehicles])

@app.route('/api/vehicles', methods=['POST'])
@token_required
def add_vehicle():
    data = request.get_json()
    conn = get_db()
    conn.execute("INSERT INTO vehicles (id, name, plate, fuel_type, color, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (data['id'], data['name'], data.get('plate', ''), data.get('fuelType', 'SP95'), data.get('color', '#3b82f6'), datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/vehicles/<vid>', methods=['DELETE'])
@token_required
def delete_vehicle(vid):
    conn = get_db()
    conn.execute('DELETE FROM fills WHERE vehicle_id = ?', (vid,))
    conn.execute('DELETE FROM vehicles WHERE id = ?', (vid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/fills', methods=['GET'])
@token_required
def get_fills():
    conn = get_db()
    fills = conn.execute("""
        SELECT f.*, v.name as vehicle_name, v.color as vehicle_color
        FROM fills f JOIN vehicles v ON f.vehicle_id = v.id ORDER BY f.date DESC
    """).fetchall()
    conn.close()
    return jsonify([dict(f) for f in fills])

@app.route('/api/fills', methods=['POST'])
@token_required
def add_fill():
    data = request.get_json()
    conn = get_db()
    photo_path = None
    if data.get('photo') and data['photo'].startswith('data:image'):
        header, encoded = data['photo'].split(',', 1)
        ext = header.split('/')[1].split(';')[0]
        filename = f"fill_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{data['vehicleId']}.{ext}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        with open(filepath, 'wb') as f:
            f.write(base64.b64decode(encoded))
        photo_path = filepath
    conn.execute("""
        INSERT INTO fills (vehicle_id, date, volume, price_per_liter, total, km, lat, lng, photo, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (data['vehicleId'], data['date'], data['volume'], data['pricePerLiter'], data['total'],
        data.get('km'), data.get('location', {}).get('lat') if data.get('location') else None,
        data.get('location', {}).get('lng') if data.get('location') else None, photo_path, datetime.now().isoformat()))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/fills/<int:fid>', methods=['DELETE'])
@token_required
def delete_fill(fid):
    conn = get_db()
    fill = conn.execute('SELECT photo FROM fills WHERE id = ?', (fid,)).fetchone()
    if fill and fill['photo'] and os.path.exists(fill['photo']):
        os.remove(fill['photo'])
    conn.execute('DELETE FROM fills WHERE id = ?', (fid,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/api/stats', methods=['GET'])
@token_required
def get_stats():
    vehicle_id = request.args.get('vehicleId', 'all')
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)
    conn = get_db()
    where = ''
    params = []
    if vehicle_id != 'all':
        where = 'AND f.vehicle_id = ?'
        params = [vehicle_id]
    month_fills = conn.execute(f"SELECT f.*, v.name as vehicle_name FROM fills f JOIN vehicles v ON f.vehicle_id = v.id WHERE strftime('%Y', f.date) = ? AND strftime('%m', f.date) = ? {where} ORDER BY f.date DESC",
        [str(year), f"{month:02d}"] + params).fetchall()
    year_fills = conn.execute(f"SELECT f.*, v.name as vehicle_name FROM fills f JOIN vehicles v ON f.vehicle_id = v.id WHERE strftime('%Y', f.date) = ? {where} ORDER BY f.date DESC",
        [str(year)] + params).fetchall()
    last12 = conn.execute(f"SELECT strftime('%Y-%m', f.date) as month, SUM(f.volume) as total_volume, SUM(f.total) as total_cost, AVG(f.price_per_liter) as avg_price, COUNT(*) as count FROM fills f WHERE f.date >= date('now', '-12 months') {where.replace('AND f.vehicle_id', 'AND f.vehicle_id')} GROUP BY strftime('%Y-%m', f.date) ORDER BY month",
        params).fetchall()
    conn.close()
    return jsonify({'month': [dict(f) for f in month_fills], 'year': [dict(f) for f in year_fills], 'last12': [dict(r) for r in last12]})

@app.route('/api/export/csv', methods=['GET'])
@token_required
def export_csv():
    conn = get_db()
    fills = conn.execute("SELECT f.*, v.name as vehicle_name, v.plate as vehicle_plate FROM fills f JOIN vehicles v ON f.vehicle_id = v.id ORDER BY f.date DESC").fetchall()
    conn.close()
    output = BytesIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Vehicule', 'Immat', 'Volume_L', 'Prix_L_EUR', 'Total_EUR', 'KM', 'Lat', 'Lng'])
    for f in fills:
        writer.writerow([f['date'], f['vehicle_name'], f['vehicle_plate'], f['volume'], f['price_per_liter'], f['total'], f['km'] or '', f['lat'] or '', f['lng'] or ''])
    output.seek(0)
    return send_file(output, mimetype='text/csv', as_attachment=True, download_name='fueltrack_export.csv')

@app.route('/api/export/json', methods=['GET'])
@token_required
def export_json():
    conn = get_db()
    vehicles = conn.execute('SELECT * FROM vehicles').fetchall()
    fills = conn.execute('SELECT * FROM fills').fetchall()
    conn.close()
    data = {'vehicles': [dict(v) for v in vehicles], 'fills': [dict(f) for f in fills], 'exported_at': datetime.now().isoformat()}
    output = BytesIO()
    output.write(json.dumps(data, indent=2, ensure_ascii=False).encode('utf-8'))
    output.seek(0)
    return send_file(output, mimetype='application/json', as_attachment=True, download_name='fueltrack_backup.json')

@app.route('/api/import', methods=['POST'])
@token_required
def import_data():
    data = request.get_json()
    conn = get_db()
    for v in data.get('vehicles', []):
        conn.execute("INSERT OR REPLACE INTO vehicles (id, name, plate, fuel_type, color, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (v['id'], v['name'], v.get('plate', ''), v.get('fuel_type', 'SP95'), v.get('color', '#3b82f6'), v.get('created_at', datetime.now().isoformat())))
    for f in data.get('fills', []):
        conn.execute("INSERT OR REPLACE INTO fills (id, vehicle_id, date, volume, price_per_liter, total, km, lat, lng, photo, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (f.get('id'), f['vehicle_id'], f['date'], f['volume'], f['price_per_liter'], f['total'], f.get('km'), f.get('lat'), f.get('lng'), f.get('photo'), f.get('created_at', datetime.now().isoformat())))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'imported': {'vehicles': len(data.get('vehicles', [])), 'fills': len(data.get('fills', []))}})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=False)
