"""Private support tickets with atomic claiming, conversation and audit history."""
import time, json
import gameplay_v29.pn_world as world, gameplay_v29.pn_admin as staff
CATEGORIES = ('Kural ihlali', 'İç mekan / Bug', 'Eşya problemi', 'Genel soru', 'Araç sorunu', 'Diğer')

def schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS pn_report_messages(id INTEGER PRIMARY KEY,report_id INTEGER NOT NULL,user_id INTEGER NOT NULL,name TEXT NOT NULL,staff INTEGER NOT NULL,body TEXT NOT NULL,created REAL NOT NULL)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_report_thread ON pn_report_messages(report_id,id)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_report_events(id INTEGER PRIMARY KEY,report_id INTEGER NOT NULL,actor INTEGER NOT NULL,kind TEXT NOT NULL,created REAL NOT NULL)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_report_event_ticket ON pn_report_events(report_id,id)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_report_reads(report_id INTEGER NOT NULL,user_id INTEGER NOT NULL,last_id INTEGER NOT NULL DEFAULT 0,PRIMARY KEY(report_id,user_id))')
    cols = {r[1] for r in db.execute('PRAGMA table_info(pn_reports)')}
    for n, t in [('subject', "TEXT NOT NULL DEFAULT ''"), ('updated', 'REAL NOT NULL DEFAULT 0'), ('rating', 'INTEGER NOT NULL DEFAULT 0')]:
        if n not in cols:
            db.execute('ALTER TABLE pn_reports ADD COLUMN ' + n + ' ' + t)

def dispatch(path, uid, token, v, p):
    from gameplay_v29.pn_multiplayer import rate
    action = path.rsplit('/', 1)[-1]
    level = staff.rank(uid)
    now = time.time()

    def text(key, lo, hi):
        s = v.get(key, '')
        if not isinstance(s, str) or not lo <= len(s.strip()) <= hi:
            raise ValueError(f'{key}: {lo}–{hi} karakter gerekli.')
        return s.strip()
    with world.database() as db:
        schema(db)

        def event(rid, kind):
            db.execute('INSERT INTO pn_report_events(report_id,actor,kind,created) VALUES(?,?,?,?)', (rid, uid, kind, now))

        def message(rid, body):
            return db.execute('INSERT INTO pn_report_messages(report_id,user_id,name,staff,body,created) VALUES(?,?,?,?,?,?)', (rid, uid, p['name'] if p else 'Destek ekibi' if level else 'Talep sahibi', int(bool(level)), body, now)).lastrowid
        if action == 'create':
            if not p:
                raise ValueError('Rapor için karakterinle oyuna gir.')
            body = text('body', 5, 1000)
            subject = v.get('subject', body[:64]).strip()
            category = v.get('category', 'Genel soru')
            if category not in CATEGORIES or not 3 <= len(subject) <= 80:
                raise ValueError('Kategori ve 3–80 karakterlik başlık gerekli.')
            if db.execute("SELECT COUNT(*) FROM pn_reports WHERE user_id=? AND status='open'", (uid,)).fetchone()[0] >= 3:
                raise ValueError('En fazla 3 açık talebin olabilir.')
            rate(token, 'report-create', 60)
            rid = db.execute('INSERT INTO pn_reports(user_id,char_id,name,body,created,category,subject,updated) VALUES(?,?,?,?,?,?,?,?)', (uid, p['char_id'], p['name'], body, now, category, subject, now)).lastrowid
            message(rid, body)
            event(rid, 'created')
            return dict(success=True, id=rid, notice=f'Talep #{rid} destek sırasına alındı.')
        if action == 'list':
            offset = staff.number(v.get('offset', 0), 0, 10000)
            status = v.get('status', 'all')
            q = str(v.get('query', ''))[:80]
            if status not in ('all', 'open', 'closed', 'mine'):
                raise ValueError('Geçersiz filtre.')
            where = ['1=1']
            args = []
            if not level:
                where.append('user_id=?')
                args.append(uid)
            if status in ('open', 'closed'):
                where.append('status=?')
                args.append(status)
            if status == 'mine' and level:
                where.append('claimed_by=?')
                args.append(uid)
            if q:
                where.append('(subject LIKE ? OR body LIKE ? OR name LIKE ?)')
                args.extend(['%' + q + '%'] * 3)
            clause = ' AND '.join(where)
            total = db.execute('SELECT COUNT(*) FROM pn_reports WHERE ' + clause, args).fetchone()[0]
            rows = [dict(r) for r in db.execute('SELECT * FROM pn_reports WHERE ' + clause + " ORDER BY CASE status WHEN 'open' THEN 0 ELSE 1 END,updated DESC,id DESC LIMIT 20 OFFSET ?", [*args, offset])]
            for r in rows:
                r['unread'] = db.execute('SELECT COUNT(*) FROM pn_report_messages WHERE report_id=? AND user_id<>? AND id>COALESCE((SELECT last_id FROM pn_report_reads WHERE report_id=? AND user_id=?),0)', (r['id'], uid, r['id'], uid)).fetchone()[0]
                r['assigned_to_me'] = r['claimed_by'] == uid
                r['subject'] = r['subject'] or r['body'][:64]
            summary = {r['status']: r['n'] for r in db.execute('SELECT status,COUNT(*) n FROM pn_reports ' + ('' if level else 'WHERE user_id=? ') + 'GROUP BY status', () if level else (uid,))}
            return dict(success=True, staff=bool(level), reports=rows, total=total, offset=offset, summary=summary, categories=CATEGORIES)
        rid = staff.number(v.get('id'), 1, 2147483647)
        r = db.execute('SELECT * FROM pn_reports WHERE id=?', (rid,)).fetchone()
        if not r or (not level and r['user_id'] != uid):
            raise ValueError('Destek talebi bulunamadı.')
        if action == 'thread':
            before = staff.number(v.get('before', 2 ** 53 - 1), 1, 2 ** 53 - 1)
            rows = [dict(x) for x in db.execute('SELECT id,name,staff,body,created FROM pn_report_messages WHERE report_id=? AND id<? ORDER BY id DESC LIMIT 60', (rid, before))]
            if not rows and r['body']:
                rows = [dict(id=0, name=r['name'], staff=0, body=r['body'], created=r['created'])] + ([dict(id=0, name='Destek ekibi', staff=1, body=r['reply'], created=r['created'])] if r['reply'] else [])
            latest = db.execute('SELECT MAX(id) FROM pn_report_messages WHERE report_id=?', (rid,)).fetchone()[0] or 0
            db.execute('INSERT INTO pn_report_reads VALUES(?,?,?) ON CONFLICT(report_id,user_id) DO UPDATE SET last_id=MAX(last_id,excluded.last_id)', (rid, uid, latest))
            events = [dict(x) for x in db.execute('SELECT kind,created FROM pn_report_events WHERE report_id=? ORDER BY id DESC LIMIT 30', (rid,))]
            return dict(success=True, report=dict(r), messages=sorted(rows, key=lambda x: x['id']), events=events, staff=bool(level), mine=r['claimed_by'] == uid, has_more=len(rows) == 60)
        if action == 'claim':
            if not level:
                raise ValueError('Rapor üstlenme yetkin yok.')
            if not db.execute("UPDATE pn_reports SET claimed_by=?,updated=? WHERE id=? AND status='open' AND claimed_by IN(0,?)", (uid, now, rid, uid)).rowcount:
                raise ValueError('Talep başka bir yetkilide veya kapalı.')
            event(rid, 'claimed')
        elif action == 'release':
            if not level or (r['claimed_by'] != uid and level < 3):
                raise ValueError('Talebi yalnız üstlenen yetkili bırakabilir.')
            db.execute('UPDATE pn_reports SET claimed_by=0,updated=? WHERE id=?', (now, rid))
            event(rid, 'released')
        elif action in ('message', 'resolve'):
            if r['status'] != 'open':
                raise ValueError('Kapalı talebe mesaj gönderilemez.')
            if action == 'resolve' and (not level):
                raise ValueError('Sonuçlandırma yetkin yok.')
            if level and r['claimed_by'] not in (0, uid) and (level < 3):
                raise ValueError('Bu taleple başka bir yetkili ilgileniyor.')
            body = text('reply' if action == 'resolve' else 'body', 2, 1000)
            rate(token, 'report-message', 1)
            message(rid, body)
            db.execute('UPDATE pn_reports SET updated=? WHERE id=?', (now, rid))
            if action == 'resolve':
                db.execute("UPDATE pn_reports SET status='closed',reply=?,actor=?,claimed_by=? WHERE id=?", (body, uid, uid, rid))
                event(rid, 'resolved')
        elif action == 'cancel':
            if uid != r['user_id']:
                raise ValueError('Yalnız kendi talebini iptal edebilirsin.')
            if r['status'] != 'open':
                raise ValueError('Talep zaten kapalı.')
            db.execute("UPDATE pn_reports SET status='closed',updated=? WHERE id=?", (now, rid))
            event(rid, 'cancelled')
        elif action == 'reopen':
            if uid != r['user_id'] and (not level):
                raise ValueError('Bu talebi açamazsın.')
            if r['status'] != 'closed' or now - max(r['updated'], r['created']) > 7 * 86400:
                raise ValueError('Yalnız son 7 gündeki kapalı talepler yeniden açılabilir.')
            if db.execute("SELECT COUNT(*) FROM pn_reports WHERE user_id=? AND status='open'", (r['user_id'],)).fetchone()[0] >= 3:
                raise ValueError('Açık talep sınırı dolu.')
            rate(token, 'report-reopen', 30)
            db.execute("UPDATE pn_reports SET status='open',claimed_by=0,updated=? WHERE id=?", (now, rid))
            event(rid, 'reopened')
        elif action == 'rate':
            value = staff.number(v.get('rating'), 1, 5)
            if uid != r['user_id'] or r['status'] != 'closed' or (not r['actor']) or r['rating']:
                raise ValueError('Sonuçlanan talebini bir kez değerlendirebilirsin.')
            db.execute('UPDATE pn_reports SET rating=? WHERE id=?', (value, rid))
            event(rid, 'rated')
        else:
            raise ValueError('Destek işlemi bulunamadı.')
        world.audit(db, uid, 'support-' + action, dict(id=rid))
    return dict(success=True, notice='Destek talebi güncellendi.')
