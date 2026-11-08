"""Character phone numbers, private SMS/contacts and accepted voice calls."""
import json, time, secrets
import gameplay_v29.pn_world as world, gameplay_v29.pn_roleplay as rp

def schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS pn_phone_contacts(char_id INTEGER NOT NULL,number INTEGER NOT NULL,name TEXT NOT NULL,PRIMARY KEY(char_id,number))')
    db.execute('CREATE TABLE IF NOT EXISTS pn_phone_messages(id INTEGER PRIMARY KEY,sender INTEGER NOT NULL,target INTEGER NOT NULL,body TEXT NOT NULL,created REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_calls(id TEXT PRIMARY KEY,caller INTEGER NOT NULL,target INTEGER NOT NULL,state TEXT NOT NULL,created REAL NOT NULL,updated REAL NOT NULL)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_sms_target ON pn_phone_messages(target,id)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_sms_sender ON pn_phone_messages(sender,id)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_call_caller ON pn_calls(caller,state,updated)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_call_target ON pn_calls(target,state,updated)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_call_expiry ON pn_calls(state,updated,created)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_sms_pair ON pn_phone_messages(sender,target,id)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_phone_reads(char_id INTEGER NOT NULL,peer INTEGER NOT NULL,last_id INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(char_id,peer))')
    db.execute('CREATE TABLE IF NOT EXISTS pn_phone_numbers(char_id INTEGER PRIMARY KEY,number INTEGER NOT NULL UNIQUE)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_phone_migrations(key TEXT PRIMARY KEY)')
    if not db.execute("SELECT 1 FROM pn_phone_migrations WHERE key='random-v22'").fetchone():
        for r in db.execute('SELECT id FROM characters').fetchall():
            _number(db, r['id'])
        for r in db.execute('SELECT char_id,number,name FROM pn_phone_contacts').fetchall():
            old = r['number'] - 500000
            if db.execute('SELECT 1 FROM characters WHERE id=?', (old,)).fetchone():
                db.execute('DELETE FROM pn_phone_contacts WHERE char_id=? AND number=?', (r['char_id'], r['number']))
                db.execute('INSERT OR IGNORE INTO pn_phone_contacts VALUES(?,?,?)', (r['char_id'], _number(db, old), r['name']))
        db.execute("INSERT INTO pn_phone_migrations VALUES('random-v22')")

def call_peer(cid):
    with world.database() as db:
        r = db.execute("SELECT * FROM pn_calls WHERE (caller=? OR target=?) AND state='active' AND updated>? ORDER BY updated DESC LIMIT 1", (cid, cid, time.time() - 30)).fetchone()
    if r and has_phone(r['caller']) and has_phone(r['target']):
        return r['target'] if r['caller'] == cid else r['caller']
    return 0

def _number(db, cid):
    row = db.execute('SELECT number FROM pn_phone_numbers WHERE char_id=?', (cid,)).fetchone()
    if row:
        return row['number']
    for _ in range(100):
        n = secrets.randbelow(60000000) + 20000000
        if not db.execute('SELECT 1 FROM pn_phone_numbers WHERE number=?', (n,)).fetchone():
            db.execute('INSERT INTO pn_phone_numbers VALUES(?,?)', (cid, n))
            return n
    raise ValueError('Telefon hattı şu anda üretilemedi.')

def number(cid):
    with world.database() as db:
        return _number(db, cid)

def has_phone(cid):
    with world.database() as db:
        r = db.execute('SELECT state FROM pn_loadout WHERE char_id=?', (cid,)).fetchone()
    return bool(r and json.loads(r['state']).get('stock', {}).get('phone', 0))

def dispatch(path, uid, token, v, p, state, presences):
    import gameplay_v29.pn_multiplayer as mp
    world.live(p, state)
    cid = p['char_id']
    action = path.rsplit('/', 1)[-1]
    now = time.time()
    with world.database() as db:
        db.execute("UPDATE pn_calls SET state='ended' WHERE (state='ringing' AND created<?) OR (state='active' AND updated<?)", (now - 30, now - 30))
        if action == 'status':
            contacts = [dict(r) for r in db.execute('SELECT number,name FROM pn_phone_contacts WHERE char_id=? ORDER BY name', (cid,))]
            recent = {r['id']: dict(r) for side in ('sender', 'target') for r in db.execute('SELECT id,sender,target,body,created FROM pn_phone_messages WHERE ' + side + '=? ORDER BY id DESC LIMIT 80', (cid,))}
            rows = sorted(recent.values(), key=lambda r: r['id'], reverse=True)[:80]
            reads = {r['peer']: r['last_id'] for r in db.execute('SELECT peer,last_id FROM pn_phone_reads WHERE char_id=?', (cid,))}
            unread = sum((r['target'] == cid and r['id'] > reads.get(r['sender'], 0) for r in rows))
            for r in rows:
                r['sender'] = _number(db, r['sender'])
                r['target'] = _number(db, r['target'])
            call = db.execute("SELECT * FROM pn_calls WHERE (caller=? OR target=?) AND state IN('ringing','active') ORDER BY created DESC LIMIT 1", (cid, cid)).fetchone()
            if call and (not has_phone(call['caller']) or not has_phone(call['target'])):
                db.execute("UPDATE pn_calls SET state='ended',updated=? WHERE id=?", (now, call['id']))
                call = None
            history = [dict(r) for r in db.execute('SELECT id,caller,target,state,created,updated FROM pn_calls WHERE (caller=? OR target=?) ORDER BY created DESC LIMIT 20', (cid, cid))]
            for r in history:
                r['caller'] = _number(db, r['caller'])
                r['target'] = _number(db, r['target'])
            return dict(success=True, number=_number(db, cid), has_phone=has_phone(cid), contacts=contacts, messages=rows, unread=unread, call_history=history, call=dict(call, peer_number=_number(db, call['target'] if call['caller'] == cid else call['caller'])) if call and has_phone(cid) else None, cash=world.wallet(uid), bank=(db.execute('SELECT balance FROM pn_bank WHERE user_id=?', (uid,)).fetchone() or {'balance': 0})['balance'])
        if not has_phone(cid):
            raise ValueError('Önce Digital Den mağazasından telefon satın al.')
        if action == 'contact-delete':
            n = rp.integer(v.get('number'), 500001, 2 ** 31 - 1)
            db.execute('DELETE FROM pn_phone_contacts WHERE char_id=? AND number=?', (cid, n))
            return dict(success=True, notice='Kişi rehberden kaldırıldı.')
        if action in ('contact', 'message', 'call', 'thread', 'read'):
            n = rp.integer(v.get('number'), 10000000, 99999999)
            line = db.execute('SELECT char_id FROM pn_phone_numbers WHERE number=?', (n,)).fetchone()
            target = line['char_id'] if line else 0
            if not db.execute('SELECT 1 FROM characters WHERE id=? AND id NOT IN(SELECT char_id FROM pn_character_archive)', (target,)).fetchone():
                raise ValueError('Telefon numarası bulunamadı.')
            if target == cid:
                raise ValueError('Kendi numaranı kullanamazsın.')
            if action == 'thread':
                before = rp.integer(v.get('before', 2 ** 53 - 1), 1, 2 ** 53 - 1)
                rows = [dict(r) for r in db.execute('SELECT id,sender,target,body,created FROM pn_phone_messages WHERE id<? AND ((sender=? AND target=?) OR (sender=? AND target=?)) ORDER BY id DESC LIMIT 40', (before, cid, target, target, cid))]
                for r in rows:
                    r['sender'] = _number(db, r['sender'])
                    r['target'] = _number(db, r['target'])
                return dict(success=True, messages=rows, has_more=len(rows) == 40)
            if action == 'read':
                last = rp.integer(v.get('last_id'), 1, 2 ** 53 - 1)
                row = db.execute('SELECT MAX(id) AS id FROM pn_phone_messages WHERE sender=? AND target=? AND id<=?', (target, cid, last)).fetchone()
                if row['id']:
                    db.execute('INSERT INTO pn_phone_reads VALUES(?,?,?) ON CONFLICT(char_id,peer) DO UPDATE SET last_id=MAX(last_id,excluded.last_id)', (cid, target, row['id']))
                return dict(success=True)
            if action == 'contact':
                if not db.execute('SELECT 1 FROM pn_phone_contacts WHERE char_id=? AND number=?', (cid, n)).fetchone() and db.execute('SELECT COUNT(*) FROM pn_phone_contacts WHERE char_id=?', (cid,)).fetchone()[0] >= 100:
                    raise ValueError('Rehberde en fazla 100 kişi olabilir.')
                name = rp.label(v.get('name'), 2, 32)
                db.execute('INSERT INTO pn_phone_contacts VALUES(?,?,?) ON CONFLICT(char_id,number) DO UPDATE SET name=excluded.name', (cid, n, name))
                return dict(success=True, notice='Kişi kaydedildi.')
            if action == 'message':
                body = rp.label(v.get('body'), 1, 400)
                mp.rate(token, 'sms', 1)
                db.execute('INSERT INTO pn_phone_messages(sender,target,body,created) VALUES(?,?,?,?)', (cid, target, body, now))
                return dict(success=True, notice='Mesaj gönderildi.')
            peer = next((r for r in presences.values() if r['char_id'] == target and now - r['last_seen'] < 10), None)
            if not peer or not has_phone(target):
                raise ValueError('Aradığın kişiye şu anda ulaşılamıyor.')
            if db.execute("SELECT 1 FROM pn_calls WHERE state IN('ringing','active') AND (caller IN(?,?) OR target IN(?,?))", (cid, target, cid, target)).fetchone():
                raise ValueError('Hat meşgul.')
            mp.rate(token, 'phone-call', 3)
            id = secrets.token_hex(12)
            db.execute("INSERT INTO pn_calls VALUES(?,?,?,'ringing',?,?)", (id, cid, target, now, now))
            return dict(success=True, notice='Aranıyor…')
        if action in ('accept', 'hangup', 'heartbeat'):
            r = db.execute('SELECT * FROM pn_calls WHERE id=?', (v.get('id'),)).fetchone()
            if not r or cid not in (r['caller'], r['target']):
                raise ValueError('Arama bulunamadı.')
            if action == 'accept':
                if cid != r['target'] or r['state'] != 'ringing':
                    raise ValueError('Bu aramayı kabul edemezsin.')
                db.execute("UPDATE pn_calls SET state='active',updated=? WHERE id=?", (now, r['id']))
            elif action == 'hangup':
                db.execute("UPDATE pn_calls SET state='ended',updated=? WHERE id=?", (now, r['id']))
            elif r['state'] in ('ringing', 'active'):
                db.execute('UPDATE pn_calls SET updated=? WHERE id=?', (now, r['id']))
            return dict(success=True)
    raise ValueError('Telefon işlemi bulunamadı.')
