"""Faction-scoped text and existing consent-based PCM voice transport."""
import importlib
import time

def install(api):
    if getattr(api,'radio61_installed',False):return api
    multi=importlib.import_module(api.__package__+'.pn_multiplayer')
    phone=importlib.import_module(api.__package__+'.pn_phone')
    previous=api.dispatch;voice=multi.voice;audio=multi.audio;messages=multi.messages
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_radio61(id INTEGER PRIMARY KEY,faction_id INTEGER NOT NULL,char_id INTEGER NOT NULL,name TEXT NOT NULL,body TEXT NOT NULL,created REAL NOT NULL)')
        db.execute('CREATE INDEX IF NOT EXISTS pn_radio_recent61 ON pn_radio61(faction_id,created)')
    def member(cid):
        with api.database() as db:
            r=db.execute('SELECT faction_id FROM pn_faction_members WHERE char_id=?',(cid,)).fetchone()
        return r['faction_id'] if r else 0
    def enabled(cid):
        return next((p for p in api.PRESENCE.values() if p['char_id']==cid and p.get('radio61') and time.time()-p['last_seen']<20),None)
    def speak(token,payload,p,s):
        result=voice(token,payload,p,s)
        if result.get('success') and p.get('radio61') and not phone.call_peer(p['char_id']):
            fid=member(p['char_id'])
            if fid and multi.VOICE and multi.VOICE[-1]['char_id']==p['char_id']:
                multi.VOICE[-1]['radio61']=fid
        return result
    def listen(s,cursor):
        base=audio(s,cursor)
        if not enabled(s['char_id']) or phone.call_peer(s['char_id']):return base
        fid=member(s['char_id'])
        if not fid:return base
        seen={v['seq'] for v in base};now=time.time()
        extra=[dict(v,age=max(0,now-v['time']),x=s['x'],y=s['y'],z=s['z'],phone=True) for v in multi.VOICE if v['seq']>cursor and v['seq'] not in seen and v['char_id']!=s['char_id'] and v.get('radio61')==fid and now-v['time']<2]
        return sorted(base+extra,key=lambda v:v['seq'])[-64:]
    def text(s):
        rows=messages(s)
        if not enabled(s['char_id']):return rows
        fid=member(s['char_id'])
        if not fid:return rows
        with api.database() as db:
            extra=[dict(r,scope='radio',name='[Telsiz] '+r['name']) for r in db.execute('SELECT id,char_id,name,body,created FROM pn_radio61 WHERE faction_id=? AND created>? ORDER BY id DESC LIMIT 30',(fid,time.time()-300))]
        return sorted(rows+extra,key=lambda r:r['id'])[-80:]
    def dispatch(path,payload,token):
        with api.LOCK:
            p=api.PRESENCE.get(token)
            if path=='/api/chat/send' and p and api.authenticated61(token):
                api.require_client61(token,payload)
                parts=str(payload.get('message','')).strip().split(None,1);cmd=parts[0].lower() if parts else ''
                if cmd in ('/r','/telsiz'):
                    api.world.live(p,api.GTA_STATE.get(token));fid=member(p['char_id'])
                    if not fid:raise ValueError('Telsiz için bir birliğe üye olmalısın.')
                    if cmd=='/telsiz':
                        p['radio61']=not p.get('radio61',False)
                        return dict(success=True,notice='Birlik telsizi '+('açık. Z ile konuş; /r mesaj ile yaz.' if p['radio61'] else 'kapalı.'),radio61=p['radio61']),None
                    if not p.get('radio61'):raise ValueError('Önce /telsiz ile birlik telsizini aç.')
                    if len(parts)<2 or not 1<=len(parts[1])<=200:raise ValueError('Kullanım: /r mesaj (en fazla 200 karakter)')
                    multi.rate(token,'radio61',.6)
                    with api.database() as db:
                        mid=db.execute("INSERT INTO pn_chat(char_id,name,body,scope,x,y,z,created) VALUES(?,?,'','local',0,0,0,0)",(p['char_id'],p['name'])).lastrowid
                        db.execute('DELETE FROM pn_chat WHERE id=?',(mid,))
                        db.execute('INSERT INTO pn_radio61 VALUES(?,?,?,?,?,?)',(mid,fid,p['char_id'],p['name'],parts[1],time.time()))
                        db.execute('DELETE FROM pn_radio61 WHERE created<?',(time.time()-86400,))
                    return dict(success=True,notice='Birlik telsizine gönderildi.'),None
            result,cookie=previous(path,payload,token)
            if result.get('success') and p and path=='/api/gta/sync':result['radio61']=bool(p.get('radio61'))
            return result,cookie
    api.dispatch=dispatch;multi.voice=speak;multi.audio=listen;multi.messages=text;api.radio61_installed=True
    return api
