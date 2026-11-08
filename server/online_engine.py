"""PAVCITY Los Santos Online - Database & Multiplayer Engine"""
import sqlite3
import time
import json
import hashlib
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'online.db')

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at REAL NOT NULL
        )
    ''')
    # Characters table
    c.execute('''
        CREATE TABLE IF NOT EXISTS characters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            surname TEXT NOT NULL,
            role TEXT NOT NULL,
            gender TEXT DEFAULT 'male',
            cash INTEGER DEFAULT 5000,
            bank INTEGER DEFAULT 25000,
            spawn_location TEXT DEFAULT 'Legion Square',
            pos_x REAL DEFAULT 215.7,
            pos_y REAL DEFAULT -920.3,
            pos_z REAL DEFAULT 30.6,
            kills INTEGER DEFAULT 0,
            deaths INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    # Chat / Logs table
    c.execute('''
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            char_id INTEGER,
            sender_name TEXT NOT NULL,
            role TEXT NOT NULL,
            message TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# In-memory transient player sync state
# { char_id: { 'user_id': ..., 'name': ..., 'role': ..., 'pos_x': ..., 'pos_y': ..., 'pos_z': ..., 'health': ..., 'last_seen': ... } }
ACTIVE_PLAYERS = {}

def hash_pw(password):
    if not password:
        password = ''
    return hashlib.sha256(str(password).encode('utf-8')).hexdigest()

def register_user(username, password):
    if not username or not password or len(str(username).strip()) < 3 or len(str(password)) < 3:
        return {'success': False, 'error': 'Kullanıcı adı ve şifre en az 3 karakter olmalıdır'}
    conn = get_db()
    c = conn.cursor()
    try:
        pw_hash = hash_pw(password)
        c.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)', 
                  (str(username).strip(), pw_hash, time.time()))
        user_id = c.lastrowid
        conn.commit()
        return {'success': True, 'user_id': user_id, 'username': str(username).strip()}
    except sqlite3.IntegrityError:
        return {'success': False, 'error': 'Bu kullanıcı adı zaten kayıtlı! Başka bir isim deneyin veya Giriş Yapın.'}
    finally:
        conn.close()

def login_user(username, password):
    if not username or not password:
        return {'success': False, 'error': 'Lütfen kullanıcı adı ve şifrenizi giriniz'}
    conn = get_db()
    c = conn.cursor()
    try:
        pw_hash = hash_pw(password)
        c.execute('SELECT id, username FROM users WHERE username = ? AND password_hash = ?', (str(username).strip(), pw_hash))
        user = c.fetchone()
        if not user:
            return {'success': False, 'error': 'Kullanıcı adı veya şifre hatalı! Henüz kaydolmadıysanız "Kayıt Ol" sekmesini kullanın.'}
        
        user_id = user['id']
        c.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
        chars = [dict(row) for row in c.fetchall()]
        return {'success': True, 'user_id': user_id, 'username': user['username'], 'characters': chars}
    finally:
        conn.close()

def create_character(user_id, name, surname, role, gender='male', spawn='Legion Square'):
    if not name or not surname:
        return {'success': False, 'error': 'Karakter adı ve soyadı girilmelidir'}
    
    spawn_coords = {
        'Legion Square': (215.7 + ((user_id % 5) * 2.4), -920.3, 30.6),
        'Pillbox Hill': (310.2, -590.1, 43.2),
        'Sandy Shores': (1850.5, 3680.2, 33.5),
        'Paleto Bay': (-130.4, 6450.8, 31.4),
        'Vespucci Beach': (-1180.2, -1500.5, 4.3)
    }
    x, y, z = spawn_coords.get(spawn, (215.7 + ((user_id % 5) * 2.4), -920.3, 30.6))
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        INSERT INTO characters (user_id, name, surname, role, gender, cash, bank, spawn_location, pos_x, pos_y, pos_z, created_at)
        VALUES (?, ?, ?, ?, ?, 5000, 25000, ?, ?, ?, ?, ?)
    ''', (user_id, name.strip(), surname.strip(), role, gender, spawn, x, y, z, time.time()))
    char_id = c.lastrowid
    conn.commit()
    c.execute('SELECT * FROM characters WHERE id = ?', (char_id,))
    char_data = dict(c.fetchone())
    conn.close()
    return {'success': True, 'character': char_data}

def sync_player(char_id, user_id, name, role, x, y, z, health=100, is_dead=False, heading=0.0, speed=0.0, vehicle="ON FOOT", zone="Los Santos"):
    now = time.time()
    ACTIVE_PLAYERS[char_id] = {
        'char_id': char_id,
        'user_id': user_id,
        'name': name,
        'role': role,
        'pos_x': float(x),
        'pos_y': float(y),
        'pos_z': float(z),
        'health': int(health),
        'is_dead': bool(is_dead),
        'heading': float(heading),
        'speed': float(speed),
        'vehicle': str(vehicle),
        'zone': str(zone),
        'last_seen': now
    }
    
    # Prune inactive players (idle > 20s)
    cutoff = now - 20
    inactive = [cid for cid, p in ACTIVE_PLAYERS.items() if p['last_seen'] < cutoff]
    for cid in inactive:
        del ACTIVE_PLAYERS[cid]
        
    return list(ACTIVE_PLAYERS.values())

def get_active_players():
    now = time.time()
    cutoff = now - 20
    inactive = [cid for cid, p in ACTIVE_PLAYERS.items() if p['last_seen'] < cutoff]
    for cid in inactive:
        del ACTIVE_PLAYERS[cid]
    return list(ACTIVE_PLAYERS.values())

def quick_login(username):
    if not username or len(str(username).strip()) < 1:
        username = "Oyuncu"
    username = str(username).strip()
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        if not user:
            pw_hash = hash_pw("quick_pass")
            c.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)',
                      (username, pw_hash, time.time()))
            user_id = c.lastrowid
            conn.commit()
            chars = []
        else:
            user_id = user['id']
            c.execute('SELECT * FROM characters WHERE user_id = ?', (user_id,))
            chars = [dict(row) for row in c.fetchall()]
            for ch in chars:
                # Synchronize to common spawn point so all players spawn together
                slot_offset = (ch.get('id', 1) % 5) * 2.4
                ch['pos_x'] = 215.7 + slot_offset
                ch['pos_y'] = -920.3
                ch['pos_z'] = 30.6
                ch['spawn_location'] = 'Legion Square'
        return {'success': True, 'user_id': user_id, 'username': username, 'characters': chars}
    finally:
        conn.close()

def add_chat(char_id, sender_name, role, message, chat_type="ic"):
    if not message or len(message.strip()) == 0:
        return {'success': False}
    msg = message.strip()
    
    if msg.startswith('/ooc ') or msg.startswith('//'):
        chat_type = 'ooc'
        msg = msg[5:].strip() if msg.startswith('/ooc ') else msg[2:].strip()
    elif msg.startswith('/me '):
        chat_type = 'me'
        msg = msg[4:].strip()
    elif msg.startswith('/do '):
        chat_type = 'do'
        msg = msg[4:].strip()
    elif msg.startswith('/ad '):
        chat_type = 'ad'
        msg = msg[4:].strip()
        
    conn = get_db()
    c = conn.cursor()
    c.execute('PRAGMA table_info(chat_logs)')
    cols = [col[1] for col in c.fetchall()]
    if 'chat_type' not in cols:
        c.execute('ALTER TABLE chat_logs ADD COLUMN chat_type TEXT DEFAULT "ic"')
        conn.commit()
        
    c.execute('INSERT INTO chat_logs (char_id, sender_name, role, message, chat_type, timestamp) VALUES (?, ?, ?, ?, ?, ?)',
              (char_id, sender_name, role, msg, chat_type, time.time()))
    conn.commit()
    conn.close()
    return {'success': True, 'chat_type': chat_type, 'message': msg}

def get_recent_chat(limit=30):
    conn = get_db()
    c = conn.cursor()
    c.execute('PRAGMA table_info(chat_logs)')
    cols = [col[1] for col in c.fetchall()]
    if 'chat_type' in cols:
        c.execute('SELECT id, sender_name, role, message, chat_type, timestamp FROM chat_logs ORDER BY id DESC LIMIT ?', (limit,))
    else:
        c.execute('SELECT id, sender_name, role, message, "ic" as chat_type, timestamp FROM chat_logs ORDER BY id DESC LIMIT ?', (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    rows.reverse()
    return rows

def player_hit(attacker_id, attacker_name, target_id, damage=25):
    try:
        target_id = int(target_id)
        if target_id in ACTIVE_PLAYERS:
            target = ACTIVE_PLAYERS[target_id]
            new_hp = max(0, int(target.get('health', 100)) - int(damage))
            target['health'] = new_hp
            is_dead = (new_hp == 0)
            target['is_dead'] = is_dead
            kill_msg = None
            if is_dead:
                kill_msg = f"[ÖLÜM] {attacker_name}, {target.get('name', 'Bilinmeyen')}'i vurdu!"
                add_chat(attacker_id, "[SİSTEM]", "Sistem", kill_msg, chat_type="ic")
            return {'success': True, 'target_id': target_id, 'health': new_hp, 'is_dead': is_dead, 'kill_msg': kill_msg}
        return {'success': True, 'target_id': target_id, 'health': 100, 'is_dead': False}
    except Exception as e:
        return {'success': False, 'error': str(e)}


