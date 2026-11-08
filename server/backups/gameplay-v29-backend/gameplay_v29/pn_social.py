"""In-server social feed, saved public video links and fictional game exchange."""
import time, math, re, json, hashlib
import gameplay_v29.pn_world as world, gameplay_v29.pn_roleplay as rp, gameplay_v29.pn_phone as phone
SYMBOLS = {'PAV': ('PAV Motors', 450), 'LST': ('Los Santos Transit', 230), 'GRP': ('Grapeseed Tarım', 125)}

def schema(db):
    for sql in ['CREATE TABLE IF NOT EXISTS pn_social_posts(id INTEGER PRIMARY KEY,char_id INTEGER NOT NULL,name TEXT NOT NULL,body TEXT NOT NULL,created REAL NOT NULL,deleted INTEGER NOT NULL DEFAULT 0)', 'CREATE TABLE IF NOT EXISTS pn_social_likes(post_id INTEGER NOT NULL,char_id INTEGER NOT NULL,PRIMARY KEY(post_id,char_id))', 'CREATE TABLE IF NOT EXISTS pn_phone_videos(id INTEGER PRIMARY KEY,char_id INTEGER NOT NULL,title TEXT NOT NULL,video TEXT NOT NULL,created REAL NOT NULL,UNIQUE(char_id,video))', 'CREATE TABLE IF NOT EXISTS pn_game_shares(char_id INTEGER NOT NULL,symbol TEXT NOT NULL,qty INTEGER NOT NULL CHECK(qty>=0),PRIMARY KEY(char_id,symbol))']:
        db.execute(sql)

def quotes():
    t = int(time.time() // 300)
    return [dict(symbol=k, name=n, price=max(1, round(base * (1 + 0.12 * math.sin(t * 0.13 + i) + 0.04 * math.sin(t * 0.7 + i)))), updated=t * 300) for i, (k, (n, base)) in enumerate(SYMBOLS.items())]

def dispatch(path, uid, token, v, p, state):
    from gameplay_v29.pn_multiplayer import rate
    world.live(p, state)
    cid = p['char_id']
    if not phone.has_phone(cid):
        raise ValueError('Telefon satın almalısın.')
    action = path.rsplit('/', 1)[-1]
    with world.database() as db:
        schema(db)
        if action == 'feed':
            before = rp.integer(v.get('before', 2 ** 53 - 1), 1, 2 ** 53 - 1)
            rows = [dict(r) for r in db.execute('SELECT p.id,p.name,p.body,p.created,p.char_id,(SELECT COUNT(*) FROM pn_social_likes WHERE post_id=p.id) likes,EXISTS(SELECT 1 FROM pn_social_likes WHERE post_id=p.id AND char_id=?) liked FROM pn_social_posts p WHERE deleted=0 AND id<? ORDER BY id DESC LIMIT 30', (cid, before))]
            for r in rows:
                r['mine'] = r.pop('char_id') == cid
            return dict(success=True, posts=rows, has_more=len(rows) == 30)
        if action == 'post':
            body = rp.label(v.get('body'), 1, 280)
            rate(token, 'social-post', 10)
            db.execute('INSERT INTO pn_social_posts(char_id,name,body,created) VALUES(?,?,?,?)', (cid, p['name'], body, time.time()))
            return dict(success=True, notice='Şehir akışında paylaşıldı.')
        if action in ('like', 'delete'):
            id = rp.integer(v.get('id'), 1)
            r = db.execute('SELECT * FROM pn_social_posts WHERE id=? AND deleted=0', (id,)).fetchone()
            if not r:
                raise ValueError('Gönderi bulunamadı.')
            if action == 'delete':
                if r['char_id'] != cid:
                    raise ValueError('Yalnız kendi gönderini kaldırabilirsin.')
                db.execute('UPDATE pn_social_posts SET deleted=1 WHERE id=?', (id,))
            elif not db.execute('DELETE FROM pn_social_likes WHERE post_id=? AND char_id=?', (id, cid)).rowcount:
                db.execute('INSERT INTO pn_social_likes VALUES(?,?)', (id, cid))
            return dict(success=True)
        if action == 'videos':
            return dict(success=True, videos=[dict(r) for r in db.execute('SELECT id,title,video FROM pn_phone_videos WHERE char_id=? ORDER BY id DESC LIMIT 30', (cid,))])
        if action == 'video-save':
            title = rp.label(v.get('title'), 2, 64)
            video = str(v.get('video', ''))
            if not re.fullmatch('[A-Za-z0-9_-]{11}', video):
                raise ValueError('Geçerli 11 karakterlik YouTube video ID gerekli.')
            if db.execute('SELECT COUNT(*) FROM pn_phone_videos WHERE char_id=?', (cid,)).fetchone()[0] >= 30:
                raise ValueError('Video listesi sınırı 30.')
            db.execute('INSERT OR IGNORE INTO pn_phone_videos(char_id,title,video,created) VALUES(?,?,?,?)', (cid, title, video, time.time()))
            return dict(success=True)
        if action == 'video-remove':
            db.execute('DELETE FROM pn_phone_videos WHERE id=? AND char_id=?', (rp.integer(v.get('id'), 1), cid))
            return dict(success=True)
        if action == 'exchange':
            return dict(success=True, quotes=quotes(), holdings=[dict(r) for r in db.execute('SELECT symbol,qty FROM pn_game_shares WHERE char_id=?', (cid,))], cash=world.wallet(uid))
        if action == 'trade':
            symbol = v.get('symbol')
            side = v.get('side')
            qty = rp.integer(v.get('qty'), 1, 100)
            if symbol not in SYMBOLS or side not in ('buy', 'sell'):
                raise ValueError('Geçersiz oyun hissesi işlemi.')
            req = v.get('request_id')
            if not isinstance(req, str) or not 16 <= len(req) <= 80:
                raise ValueError('İşlem kimliği gerekli.')
            digest = hashlib.sha256(json.dumps([symbol, side, qty]).encode()).hexdigest()
            old = db.execute('SELECT digest,result FROM pn_rp_receipts WHERE user_id=? AND key=?', (uid, req)).fetchone()
            if old:
                if old['digest'] != digest:
                    raise ValueError('İşlem kimliği çakıştı.')
                return json.loads(old['result'])
            rate(token, 'game-trade', 1)
            quote = next((q for q in quotes() if q['symbol'] == symbol))
            total = qty * quote['price']
            r = db.execute('SELECT qty FROM pn_game_shares WHERE char_id=? AND symbol=?', (cid, symbol)).fetchone()
            owned = r['qty'] if r else 0
            if side == 'buy':
                if owned + qty > 1000:
                    raise ValueError('Oyun hissesi sınırı 1000.')
                rp.debit(db, 'pn_wallet', 'user_id', uid, total)
                remaining = owned + qty
            else:
                if owned < qty:
                    raise ValueError('Yeterli oyun hissesi yok.')
                db.execute('UPDATE pn_wallet SET balance=balance+? WHERE user_id=?', (total, uid))
                remaining = owned - qty
            db.execute('INSERT INTO pn_game_shares VALUES(?,?,?) ON CONFLICT(char_id,symbol) DO UPDATE SET qty=excluded.qty', (cid, symbol, remaining))
            result = dict(success=True, notice='Oyun hissesi işlemi kaydedildi.', price=quote['price'], qty=qty, money=world.wallet(uid))
            db.execute('INSERT INTO pn_rp_receipts VALUES(?,?,?,?,?)', (uid, req, digest, json.dumps(result), time.time()))
            world.audit(db, uid, 'game-trade', dict(symbol=symbol, side=side, qty=qty, total=total))
            return result
    raise ValueError('Telefon uygulaması işlemi bulunamadı.')
