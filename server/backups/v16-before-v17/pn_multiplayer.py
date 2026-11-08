"""Bounded multiplayer services. Caller holds session_api.LOCK.

Gameplay damage uses client native hit reports plus server distance/cooldown
checks. It is not an authoritative physics simulation or a complete anti-cheat.
Voice is transient PCM relayed by this VDS, without third-party STUN/TURN.
"""
import base64
import binascii
import json
import math
import time
import unicodedata
from collections import deque
from contextlib import contextmanager,nullcontext
import online_engine as engine

CHAT_RADIUS = {'local':25, 'me':20, 'do':20, 'ooc':40}
VOICE_RADIUS = 30
VOICE = deque(maxlen=160)
voice_sequence = 0
RATES = {}

@contextmanager
def database():
    db=engine.get_db()
    try:
        with db:yield db
    finally:db.close()

def identity(value):
    return ' '.join(unicodedata.normalize('NFKC', value).casefold().replace('\u0307','').replace('ı','i').split())

def schema(db):
    import pn_world
    pn_world.schema(db)
    db.execute('CREATE TABLE IF NOT EXISTS pn_identity(kind TEXT,key TEXT,owner INTEGER,PRIMARY KEY(kind,key))')
    db.execute('CREATE TABLE IF NOT EXISTS pn_saved(char_id INTEGER PRIMARY KEY,state TEXT NOT NULL,updated REAL NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_chat(id INTEGER PRIMARY KEY AUTOINCREMENT,char_id INTEGER,name TEXT,body TEXT,scope TEXT,x REAL,y REAL,z REAL,created REAL)')
    db.execute('CREATE INDEX IF NOT EXISTS pn_chat_recent ON pn_chat(created)')
    if 'admin' not in [r[1] for r in db.execute('PRAGMA table_info(pn_chat)')]:db.execute('ALTER TABLE pn_chat ADD COLUMN admin INTEGER NOT NULL DEFAULT 0')
    db.execute('CREATE TABLE IF NOT EXISTS pn_sessions(hash TEXT PRIMARY KEY,user_id INTEGER NOT NULL,expires REAL NOT NULL)')
    for row in db.execute('SELECT id,username FROM users ORDER BY id').fetchall():
        db.execute('INSERT OR IGNORE INTO pn_identity VALUES(?,?,?)',('account',identity(row['username']),row['id']))
    for row in db.execute('SELECT id,name,surname FROM characters ORDER BY id').fetchall():
        db.execute('INSERT OR IGNORE INTO pn_identity VALUES(?,?,?)',('character',identity(row['name']+' '+row['surname']),row['id']))

def reserve(db, kind, label, owner):
    key=identity(label)
    row=db.execute('SELECT owner FROM pn_identity WHERE kind=? AND key=?',(kind,key)).fetchone()
    if row and row['owner']!=owner:
        raise ValueError('Bu kullanıcı adı zaten alınmış.' if kind=='account' else 'Bu karakterin ad ve soyadı zaten alınmış.')
    db.execute('INSERT OR IGNORE INTO pn_identity VALUES(?,?,?)',(kind,key,owner))

def initial(character):
    with database() as db:
        schema(db)
        row=db.execute('SELECT state FROM pn_saved WHERE char_id=?',(character['id'],)).fetchone()
    saved=json.loads(row['state']) if row else {}
    state={key:saved.get(key,character.get('pos_'+key,default)) for key,default in [('x',215.7),('y',-920.3),('z',30.6),('heading',0),('health',200)]}
    state.update(hunger=max(0,min(100,float(saved.get('hunger',100)))),thirst=max(0,min(100,float(saved.get('thirst',100)))),food=max(0,int(saved.get('food',3))),water=max(0,int(saved.get('water',3))))
    state['armor']=max(0,min(100,int(saved.get('armor',0))))
    return state

def save(presence, state, force=False, connection=None):
    now=time.time()
    if not force and now-presence.get('saved_at',0)<3:return
    presence['saved_at']=now
    values={key:state[key] for key in ('x','y','z','heading','health')}
    values.update({key:presence.get(key,default) for key,default in [('hunger',100),('thirst',100),('food',3),('water',3)]})
    values['armor']=presence.get('armor',0)
    with (database() if connection is None else nullcontext(connection)) as db:
        db.execute('INSERT INTO pn_saved VALUES(?,?,?) ON CONFLICT(char_id) DO UPDATE SET state=excluded.state,updated=excluded.updated',(presence['char_id'],json.dumps(values),now))
        db.execute('UPDATE characters SET pos_x=?,pos_y=?,pos_z=? WHERE id=?',(state['x'],state['y'],state['z'],presence['char_id']))

def distance(a,b):
    return math.sqrt(sum((a[k]-b[k])**2 for k in ('x','y','z')))

def active(states, now=None):
    now=now or time.time()
    return [p for p in states.values() if now-p['last_seen']<10]

def messages(state):
    if not state:return []
    with database() as db:
        rows=db.execute('SELECT * FROM pn_chat WHERE created>? ORDER BY id DESC LIMIT 100',(time.time()-300,)).fetchall()
    return [dict(m) for m in reversed(rows) if distance(state,m)<=CHAT_RADIUS[m['scope']]]

def rate(token,key,interval):
    now=time.time();pair=(token,key)
    if now-RATES.get(pair,0)<interval:raise ValueError('Çok hızlı işlem gönderiyorsun.')
    RATES[pair]=now
    if len(RATES)>1000:
        for stale in list(RATES):
            if now-RATES[stale]>60:RATES.pop(stale,None)

def chat(token, payload, presence, state):
    if not state:raise ValueError('Sohbet için önce GTA dünyasına girin.')
    raw=str(payload.get('message','')).strip()
    scope=payload.get('scope','local')
    if raw.startswith('/'):
        pieces=raw[1:].split(None,1);command=pieces[0] if pieces else '';raw=pieces[1] if len(pieces)>1 else ''
        scope={'me':'me','do':'do','b':'ooc','ooc':'ooc'}.get(command.lower())
        if not scope:raise ValueError('Bilinmeyen komut. /yardim yaz; / ile komut önerilerini aç.')
    if scope not in CHAT_RADIUS or not 1<=len(raw.strip())<=200:raise ValueError('Mesaj 1–200 karakter olmalı.')
    rate(token,'chat',.6)
    with database() as db:
        db.execute('INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created,admin) VALUES(?,?,?,?,?,?,?,?,?)',(presence['char_id'],presence['name'],raw.strip(),scope,state['x'],state['y'],state['z'],time.time(),int(presence.get('admin_duty',False) and not presence.get('hide_admin'))))
        db.execute('DELETE FROM pn_chat WHERE created<?',(time.time()-86400,))
    return {'success':True}

def voice(token,payload,presence,state):
    global voice_sequence
    if not state:raise ValueError('Ses için önce GTA dünyasına girin.')
    data=payload.get('audio','')
    if not isinstance(data,str) or len(data)>11000:raise ValueError('Geçersiz ses paketi.')
    try:raw=base64.b64decode(data,validate=True)
    except (ValueError,binascii.Error):raise ValueError('Geçersiz ses paketi.')
    if not 320<=len(raw)<=8000 or len(raw)%2:raise ValueError('Geçersiz PCM paketi.')
    rate(token,'voice',.09)
    voice_sequence+=1
    VOICE.append(dict(seq=voice_sequence,char_id=presence['char_id'],audio=data,time=time.time(),x=state['x'],y=state['y'],z=state['z']))
    state['speaking_until']=time.time()+.7
    return {'success':True}

def audio(state,cursor):
    now=time.time()
    while VOICE and now-VOICE[0]['time']>2:VOICE.popleft()
    return [dict(v) for v in VOICE if v['seq']>cursor and v['char_id']!=state['char_id'] and distance(state,v)<=VOICE_RADIUS][-24:]

def needs(presence, now=None):
    now=time.time() if now is None else now
    elapsed=max(0,min(5,now-presence.get('needs_at',now)))
    presence['needs_at']=now
    if presence.get('health',200)>100:
        presence['hunger']=max(0,presence.get('hunger',100)-elapsed/60)
        presence['thirst']=max(0,presence.get('thirst',100)-elapsed/40)
    return {key:presence.get(key,default) for key,default in [('hunger',100),('thirst',100),('food',3),('water',3)]}

def consume(token,payload,presence,state):
    if not presence or not state or presence.get('health',200)<=100:raise ValueError('Tüketmek için hayatta ve oyunda olmalısın.')
    item=payload.get('item')
    if item not in ('food','water'):raise ValueError('Geçersiz eşya.')
    if presence.get(item,3)<=0:raise ValueError('Çantanda bu eşya kalmadı.')
    rate(token,'consume',2)
    needs(presence)
    presence[item]=presence.get(item,3)-1
    key='hunger' if item=='food' else 'thirst'
    presence[key]=min(100,presence.get(key,100)+(30 if item=='food' else 35))
    save(presence,state,True)
    return {'success':True,'needs':needs(presence)}

def update(token,payload,fields,presence,states,presences):
    now=time.time();old=states.get(token)
    life=presence.get('life_id',0)
    supplied=payload.get('life_id',life)
    if type(supplied) is not int or supplied<0 or supplied>life:raise ValueError('Geçersiz yaşam sürümü.')
    if supplied!=life and old:
        old['last_seen']=now
        # A response guard in JavaScript cannot prevent an old request from
        # mutating this database. Reject old-life health, hits and coordinates.
        return snapshot(presence,old,states,presences,presence.get('hit_sequence',0),max(0,int(payload.get('voice_cursor',0))),presence.get('respawn_spawn'))
    fields['weapon']=int(payload.get('weapon',0))&0xffffffff
    fields['flags']=int(payload.get('flags',0))&255
    import pn_interactions,pn_admin
    fields['fly']=bool(presence.get('fly') and pn_admin.rank(presence['user_id'])>=2)
    # Phone pose is cosmetic for every player; staff actions still enforce rank on the server.
    pn_interactions.clean(presences)
    pn_interactions.constrain(presence,fields,states)
    for key in ('vx','vy','vz','aim_x','aim_y','aim_z'):
        value=float(payload.get(key,0))
        if not math.isfinite(value) or abs(value)>20000:raise ValueError('Geçersiz hareket durumu.')
        fields[key]=value
    hits=payload.get('hits',[])
    if not isinstance(hits,list) or len(hits)>8:raise ValueError('Geçersiz vuruş paketi.')
    if any(not isinstance(h,dict) or not isinstance(h.get('seq'),int) or not isinstance(h.get('target'),int) or h.get('kind') not in ('melee','shoot') for h in hits):raise ValueError('Geçersiz vuruş paketi.')
    cursor=max(0,int(payload.get('voice_cursor',0)))
    import pn_world
    import pn_admin
    teleport=pn_admin.constraints(presence,fields)
    pn_world.clean_seats(presences)
    pn_world.validate_sample(presence,fields,payload)
    armor=float(payload.get('armor',presence.get('armor',0)))
    if not math.isfinite(armor):raise ValueError('Geçersiz zırh.')
    hp=presence.get('health',200)
    if now-presence.get('respawned_at',0)>.7 and 0<=fields['health']<hp:hp=fields['health']
    presence['health']=max(0,min(200,hp))
    presence['armor']=max(0,min(presence.get('armor',0),armor))
    fields['armor']=presence['armor']
    if presence['health']<=100:presence.setdefault('dead_at',now)
    fields['health']=presence['health']
    last=presence.get('hit_sequence',0)
    for hit in hits:
        seq=int(hit.get('seq',0))
        if seq<=last:continue
        last=seq
        victim=next((pair for pair in states.items() if pair[1]['char_id']==int(hit.get('target',0)) and now-pair[1]['last_seen']<10),None)
        if not victim or victim[0]==token or presence['health']<=100:continue
        melee=hit.get('kind')=='melee';limit=3 if melee else 200
        if distance(fields,victim[1])>limit or now-presence.get('last_hit_time',0)<.16:continue
        presence['last_hit_time']=now
        target_presence=presences.get(victim[0])
        if not target_presence:continue
        if target_presence.get('fly') and pn_admin.rank(target_presence['user_id'])>=2:continue
        damage=20 if melee else 25
        if not melee:
            absorbed=min(damage,target_presence.get('armor',0));target_presence['armor']=target_presence.get('armor',0)-absorbed;damage-=absorbed
            victim[1]['armor']=target_presence['armor']
        target_presence['health']=max(0,target_presence.get('health',200)-damage)
        victim[1]['health']=target_presence['health']
        target_presence['damage_sequence']=target_presence.get('damage_sequence',0)+1
        target_presence['damage_kind']=1 if melee else 2
        if target_presence['health']<=100:target_presence.setdefault('dead_at',now)
    presence['hit_sequence']=last
    fields['speaking_until']=old.get('speaking_until',0) if old else 0
    fields.update(char_id=presence['char_id'],server_id=presence['server_id'],name=presence['name'],last_seen=now)
    target=int(payload.get('melee_target',0))
    target_state=next((s for s in states.values() if s['char_id']==target and now-s['last_seen']<10 and s.get('health',200)>100),None)
    fields['melee_target']=target if fields['flags']&32 and target_state and target!=presence['char_id'] and distance(fields,target_state)<4 else 0
    fields.update(appearance=presence['appearance'],appearance_version=presence['appearance_version'],admin_duty=presence.get('admin_duty',False) and not presence.get('hide_admin'),damage_sequence=presence.get('damage_sequence',0),damage_kind=presence.get('damage_kind',0))
    pn_world.sample(presence,fields,payload)
    import pn_inventory
    pn_inventory.sample(presence,payload)
    states[token]=fields
    vitals=needs(presence,now)
    save(presence,fields)
    return snapshot(presence,fields,states,presences,last,cursor,teleport)

def snapshot(presence,fields,states,presences,last,cursor,teleport=None):
    import pn_world,pn_admin,pn_inventory
    import pn_interactions
    pn_interactions.clean(presences)
    fields['carried_by']=pn_interactions.CARRY.get(fields['char_id'],0)
    population=active(states)
    peers=sorted((p for p in population if p['char_id']!=fields['char_id'] and distance(fields,p)<350),key=lambda p:distance(fields,p))[:32]
    peers=[dict(p,carried_by=pn_interactions.CARRY.get(p['char_id'],0)) for p in peers]
    delay=max(0,5-(time.time()-presence.get('dead_at',time.time()))) if presence['health']<=100 else 0
    return {'success':True,'life_id':presence.get('life_id',0),'respawn_delay':delay,'loadout':pn_inventory.view(presence),'players':[fields]+peers,'player_count':len(population),'messages':messages(fields),'voice':audio(fields,cursor),'voice_cursor':voice_sequence,'health':presence['health'],'armor':presence['armor'],'teleport':teleport,'fly':bool(presence.get('fly') and pn_admin.rank(presence['user_id'])>=2),'jail_until':(pn_admin.jail(presence['char_id']) or {}).get('until',0),'hit_ack':last,'needs':needs(presence),**pn_world.view(presence['user_id'],presence,fields,presences)}

with database() as _db:
    schema(_db)
