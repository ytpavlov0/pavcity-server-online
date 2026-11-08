"""Persistent staff permissions, moderation and in-game reports. No client roles."""
import json
import time
import pn_world as world

RANKS={0:'Oyuncu',1:'Moderatör',2:'Yönetici',3:'Baş yönetici',4:'Kurucu'}
JAIL={'x':1690.5,'y':2565.5,'z':45.6,'heading':180}

def schema(db):
    db.execute('CREATE TABLE IF NOT EXISTS pn_staff(user_id INTEGER PRIMARY KEY,rank INTEGER NOT NULL CHECK(rank BETWEEN 1 AND 3))')
    db.execute('CREATE TABLE IF NOT EXISTS pn_bans(user_id INTEGER PRIMARY KEY,until REAL NOT NULL,reason TEXT NOT NULL,actor INTEGER NOT NULL)')
    db.execute('CREATE TABLE IF NOT EXISTS pn_jail(char_id INTEGER PRIMARY KEY,until REAL NOT NULL,reason TEXT NOT NULL,return_state TEXT NOT NULL)')
    db.execute("CREATE TABLE IF NOT EXISTS pn_reports(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,char_id INTEGER NOT NULL,name TEXT NOT NULL,body TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'open',reply TEXT NOT NULL DEFAULT '',actor INTEGER,created REAL NOT NULL)")

def rank(uid):
    with world.database() as db:
        if db.execute('SELECT 1 FROM pn_admin WHERE user_id=?',(uid,)).fetchone():return 4
        row=db.execute('SELECT rank FROM pn_staff WHERE user_id=?',(uid,)).fetchone()
    return row['rank'] if row else 0

def check(uid):
    with world.database() as db:
        row=db.execute('SELECT * FROM pn_bans WHERE user_id=?',(uid,)).fetchone()
    if row and (row['until']==0 or row['until']>time.time()):raise ValueError('Hesap yasaklı: '+row['reason'])

def target(cid):
    with world.database() as db:row=db.execute('SELECT * FROM characters WHERE id=?',(cid,)).fetchone()
    if not row:raise ValueError('Karakter ID bulunamadı.')
    return row

def number(value,lo,hi):
    try:value=int(value)
    except (TypeError,ValueError):raise ValueError('Geçerli sayı yaz.')
    if not lo<=value<=hi:raise ValueError(f'Sayı {lo}–{hi} aralığında olmalı.')
    return value

def command(uid,token,payload,p,presences,states):
    parts=str(payload.get('message','')).strip().split()
    if not parts:return None
    cmd=parts[0].lower();args=parts[1:];level=rank(uid)
    if cmd=='/stats':
        ch=target(p['char_id'])
        with world.database() as db:cars=db.execute('SELECT COUNT(*) FROM pn_vehicles WHERE owner=?',(ch['id'],)).fetchone()[0]
        return {'success':True,'info':{'title':'Karakter bilgileri','rows':[['İsim',p['name']],['Şehir ID',p['server_id']],['Karakter kaydı',ch['id']],['Yetki',RANKS[level]],['Cüzdan',f'${world.wallet(uid):,}'],['Araçlar',cars],['Can',max(0,int(p.get('health',200)-100))],['Zırh',int(p.get('armor',0))]]},'notice':f'{p["name"]} [{p["server_id"]}] · Kayıt #{ch["id"]} · {RANKS[level]} · ${world.wallet(uid):,} · {cars} araç · Can {max(0,int(p.get("health",200)-100))} · Zırh {int(p.get("armor",0))}'}
    if cmd=='/admins':
        active=[f'{v["name"]} [{v["server_id"]}] · {RANKS[rank(v["user_id"])]}' for v in presences.values() if time.time()-v['last_seen']<20 and rank(v['user_id']) and (not v.get('hide_admin') or level==4)]
        return {'success':True,'info':{'title':'Aktif yetkililer','rows':[[str(i+1),v] for i,v in enumerate(active)] or [['Durum','Şu anda görünür yetkili yok.']]},'notice':'Aktif yetkililer: '+(' | '.join(active) if active else 'Şu anda görünür yetkili yok.')}
    if cmd in ('/sethp','/revive','/goto','/gethere'):
        if level<2:raise ValueError('Bu komut için yönetici yetkisi gerekli.')
        if len(args)!=(2 if cmd=='/sethp' else 1):raise ValueError('Kullanım: '+cmd+' ID'+(' 0–100' if cmd=='/sethp' else ''))
        cid=world.resolve_player_id(args[0],presences)
        pair=next(((key,v) for key,v in presences.items() if v['char_id']==cid and time.time()-v['last_seen']<20 and key in states),None)
        if not pair:raise ValueError('Oyuncu dünyada bağlı olmalı.')
        key,peer=pair;state=states[key]
        if rank(peer['user_id'])>level:raise ValueError('Üst yetkiliye bu işlemi uygulayamazsın.')
        if cmd in ('/sethp','/revive'):
            hp=number(args[1],0,100) if cmd=='/sethp' else 100
            health_only=hp>0 and peer.get('health',200)>100
            if not health_only:world.release(cid)
            # Every authoritative health assignment starts a fenced life; stale
            # in-flight samples must not immediately undo a staff revive/sethp.
            peer['health']=100+hp if hp else 0;state['health']=peer['health']
            if not health_only:state.update(vehicle_id=0,seat=-2,carried_by=0,speed=0,vx=0,vy=0,vz=0,flags=0)
            peer['life_id']=peer.get('life_id',0)+1;peer['respawned_at']=time.time()
            peer['respawn_spawn']={k:state[k] for k in ('x','y','z','heading','health')}
            peer['respawn_spawn']['armor']=peer.get('armor',0)
            if health_only:peer['respawn_spawn']['health_only']=True
            peer.pop('dead_at',None)
            if not hp:peer['dead_at']=time.time();world.release(cid)
            from pn_multiplayer import save
            save(peer,state,True)
        else:
            if jail(p['char_id']) or jail(cid):raise ValueError('Hapis işlemi sürerken ışınlanma kullanılamaz.')
            dest=state if cmd=='/goto' else states.get(token)
            recipient=p if cmd=='/goto' else peer
            if not dest:raise ValueError('Önce dünyaya gir.')
            world.release(recipient['char_id'])
            recipient['admin_teleport']={k:dest[k] for k in ('x','y','z','heading')}
            recipient['admin_teleport']['x']+=1.5
        with world.database() as db:world.audit(db,uid,cmd[1:],{'char_id':cid,'args':args[1:]})
        return {'success':True,'notice':f'{cmd} · {peer["name"]} [{peer["server_id"]}] tamamlandı.','info':{'title':'Yönetici işlemi','rows':[['Komut',cmd],['Oyuncu',peer['name']],['ID',peer['server_id']],['Durum','Tamamlandı']]}}
    if cmd not in ('/rankver','/ban','/unban','/jail','/unjail','/fly','/hideadmin','/aduty'):return None
    required=4 if cmd=='/rankver' else 2 if cmd in ('/ban','/unban','/fly') else 1
    if level<required:raise ValueError('Bu komut için yetkin yok.')
    if cmd in ('/hideadmin','/aduty','/fly'):
        if args:raise ValueError('Kullanım: '+cmd)
        key={'/hideadmin':'hide_admin','/aduty':'admin_duty','/fly':'fly'}[cmd]
        if cmd=='/fly' and jail(p['char_id']):raise ValueError('Hapiste uçuş kullanılamaz.')
        if cmd=='/fly':world.release(p['char_id'])
        p[key]=not p.get(key,False)
        return {'success':True,'notice':{'/hideadmin':'Yönetici etiketi gizleme','/aduty':'Yönetici görevi','/fly':'Uçuş'}[cmd]+(' açıldı.' if p[key] else ' kapatıldı.')}
    if not args:raise ValueError('Karakter ID gerekli.')
    if cmd=='/unban':
        # Offline bans refer to account names (or an explicit permanent c:ID).
        with world.database() as db:
            if args[0].startswith('c:') or args[0].isdigit():
                cid=number(args[0].removeprefix('c:'),1,2147483647)
                ch=db.execute('SELECT c.* FROM characters c JOIN pn_bans b ON b.user_id=c.user_id WHERE c.id=?',(cid,)).fetchone()
            else:ch=db.execute('SELECT c.* FROM characters c JOIN users u ON u.id=c.user_id JOIN pn_bans b ON b.user_id=u.id WHERE u.username=? COLLATE NOCASE ORDER BY c.id LIMIT 1',(args[0],)).fetchone()
        if not ch:raise ValueError('Yasaklı hesap bulunamadı. Kullanım: /unban kullanıcıadı')
        cid=ch['id']
    else:cid=world.resolve_player_id(args[0],presences);ch=target(cid)
    victim=ch['user_id'];victim_rank=rank(victim)
    if victim_rank>=level:raise ValueError('Kendine veya eşit/üst yetkiliye bu işlemi uygulayamazsın.')
    if cmd=='/rankver':
        if len(args)!=2:raise ValueError('Kullanım: /rankver ID 0|1|2|3 (0=oyuncu, 1=moderatör, 2=yönetici, 3=baş yönetici)')
        value=number(args[1],0,3)
        with world.database() as db:
            db.execute('DELETE FROM pn_staff WHERE user_id=?',(victim,))
            if value:db.execute('INSERT INTO pn_staff VALUES(?,?)',(victim,value))
            world.audit(db,uid,'rankver',{'char_id':cid,'rank':value})
        for peer in presences.values():
            if peer['user_id']==victim and not value:peer.update(admin_duty=False,hide_admin=False,fly=False)
            elif peer['user_id']==victim and value<2:peer['fly']=False
        return {'success':True,'notice':f'Oyuncu #{args[0]} → {RANKS[value]}'}
    if cmd in ('/ban','/jail'):
        if len(args)<3:raise ValueError(f'Kullanım: {cmd} ID dakika sebep'+(' (0=süresiz)' if cmd=='/ban' else ''))
        minutes=number(args[1],0 if cmd=='/ban' else 1,525600 if cmd=='/ban' else 1440);reason=' '.join(args[2:])[:200]
        until=time.time()+minutes*60 if minutes else 0
        with world.database() as db:
            if cmd=='/ban':
                db.execute('INSERT INTO pn_bans VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET until=excluded.until,reason=excluded.reason,actor=excluded.actor',(victim,until,reason,uid))
                db.execute('DELETE FROM pn_sessions WHERE user_id=?',(victim,))
            else:
                state=next((s for s in states.values() if s['char_id']==cid),None)
                if not state:raise ValueError('Hapse göndermek için oyuncu bağlı olmalı.')
                old=db.execute('SELECT return_state FROM pn_jail WHERE char_id=?',(cid,)).fetchone()
                back=old['return_state'] if old else json.dumps({k:state[k] for k in ('x','y','z','heading')})
                db.execute('INSERT INTO pn_jail VALUES(?,?,?,?) ON CONFLICT(char_id) DO UPDATE SET until=excluded.until,reason=excluded.reason',(cid,until,reason,back))
            world.audit(db,uid,cmd[1:],{'char_id':cid,'minutes':minutes,'reason':reason})
        for key,peer in list(presences.items()):
            if peer['user_id']==victim and cmd=='/ban':
                from pn_multiplayer import save
                if key in states:save(peer,states[key],True)
                world.release(peer['char_id']);presences.pop(key,None);states.pop(key,None)
            elif peer['char_id']==cid:world.release(cid);peer['fly']=False
        return {'success':True,'notice':f'Oyuncu #{args[0]}: {cmd[1:]} uygulandı.'}
    if len(args)!=1:raise ValueError('Kullanım: '+cmd+' ID')
    with world.database() as db:
        if cmd=='/unban':db.execute('DELETE FROM pn_bans WHERE user_id=?',(victim,))
        else:
            row=db.execute('SELECT * FROM pn_jail WHERE char_id=?',(cid,)).fetchone()
            if row:
                for peer in presences.values():
                    if peer['char_id']==cid:peer['admin_teleport']=json.loads(row['return_state'])
            db.execute('DELETE FROM pn_jail WHERE char_id=?',(cid,))
        world.audit(db,uid,cmd[1:],{'char_id':cid})
    return {'success':True,'notice':f'#{cid}: {cmd[1:]} tamamlandı.'}

def jail(cid):
    with world.database() as db:row=db.execute('SELECT * FROM pn_jail WHERE char_id=?',(cid,)).fetchone()
    return dict(row) if row and row['until']>time.time() else None

def constraints(p,fields):
    teleport=p.pop('admin_teleport',None)
    with world.database() as db:row=db.execute('SELECT * FROM pn_jail WHERE char_id=?',(p['char_id'],)).fetchone()
    if row:
        if row['until']<=time.time():
            teleport=json.loads(row['return_state'])
            with world.database() as db:db.execute('DELETE FROM pn_jail WHERE char_id=?',(p['char_id'],))
        elif sum((fields[k]-JAIL[k])**2 for k in ('x','y','z'))>35**2:teleport=JAIL
    if teleport:fields.update(teleport);fields.update(vx=0,vy=0,vz=0,speed=0)
    return dict(teleport) if teleport else None

def reports(path,uid,token,payload,p):
    action=path.rsplit('/',1)[-1];level=rank(uid)
    if action=='create':
        if not p:raise ValueError('Rapor için karakterinle oyuna gir.')
        body=str(payload.get('body','')).strip()
        if not 5<=len(body)<=1000:raise ValueError('Rapor 5–1000 karakter olmalı.')
        from pn_multiplayer import rate
        rate(token,'report-create',60)
        with world.database() as db:
            if db.execute("SELECT COUNT(*) FROM pn_reports WHERE user_id=? AND status='open'",(uid,)).fetchone()[0]>=3:raise ValueError('En fazla 3 açık rapor olabilir.')
            rid=db.execute('INSERT INTO pn_reports(user_id,char_id,name,body,created) VALUES(?,?,?,?,?)',(uid,p['char_id'],p['name'],body,time.time())).lastrowid
        return {'success':True,'notice':f'Rapor #{rid} yetkililere iletildi.'}
    if action=='list':
        with world.database() as db:
            rows=db.execute('SELECT * FROM pn_reports '+('' if level else 'WHERE user_id=? ')+'ORDER BY id DESC LIMIT 50',() if level else (uid,)).fetchall()
        return {'success':True,'staff':bool(level),'reports':[dict(r) for r in rows]}
    if action=='resolve':
        if not level:raise ValueError('Rapor yanıtlama yetkin yok.')
        rid=number(payload.get('id'),1,2147483647);reply=str(payload.get('reply','')).strip()
        if not 2<=len(reply)<=500:raise ValueError('Yanıt 2–500 karakter olmalı.')
        with world.database() as db:
            if not db.execute("UPDATE pn_reports SET status='closed',reply=?,actor=? WHERE id=? AND status='open'",(reply,uid,rid)).rowcount:raise ValueError('Açık rapor bulunamadı.')
            world.audit(db,uid,'report-resolve',{'id':rid})
        return {'success':True,'notice':'Rapor yanıtlandı ve kapatıldı.'}
    raise ValueError('Rapor işlemi bulunamadı.')
