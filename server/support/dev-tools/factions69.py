"""Nearby faction consent and atomic RP mutations. Installed after retail68."""
import copy
import importlib
import math
import secrets
import time


def install(api):
    if getattr(api, 'factions69_installed', False):
        return api
    rp = importlib.import_module(api.__package__ + '.pn_roleplay')
    old_action, old_view, old_dispatch = rp.faction_action, rp.faction_view, rp.dispatch
    with api.database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS pn_inviter69(invite TEXT PRIMARY KEY, char_id INTEGER NOT NULL)')

    def peer(cid):
        for token, p in api.PRESENCE.items():
            s = api.GTA_STATE.get(token)
            if p.get('char_id') == cid and p.get('world') == 'gta' and s and s.get('char_id') == cid:
                if time.time() - min(p.get('last_seen', 0), s.get('last_seen', 0)) <= 10 and p.get('health', 0) > 100:
                    return p, s
        return None

    def together(a, b):
        left, right = peer(a), peer(b)
        if not left or not right or a == b:
            return False
        p, s = left; q, t = right
        return (p.get('dimension', 0) == q.get('dimension', 0)
                and not any(x.get('property45_used', {}).get('phase') == 'pending' for x in (p, q))
                and not any(x.get('vehicle_id') for x in (s, t))
                and not api.world.occupation(a)[0] and not api.world.occupation(b)[0]
                and math.dist([s[k] for k in ('x', 'y', 'z')], [t[k] for k in ('x', 'y', 'z')]) <= 5)

    def view(db, cid):
        result = old_view(db, cid)
        # Old unbound invitations cannot outlive their original leader's authority.
        result['invites'] = [dict(r) for r in db.execute('''SELECT i.id,i.expires,f.name,f.tag,
          x.char_id AS inviter,c.name||' '||c.surname AS inviter_name FROM pn_faction_invites i
          JOIN pn_inviter69 x ON x.invite=i.id JOIN pn_factions f ON f.id=i.faction_id
          JOIN pn_faction_members m ON m.char_id=x.char_id AND m.faction_id=i.faction_id AND m.leader=1
          JOIN characters c ON c.id=x.char_id WHERE i.char_id=? AND i.expires>?''', (cid,time.time()))]
        for invite in result['invites']:
            invite['nearby'] = together(cid, invite['inviter'])
        result['nearby'] = []
        result['outgoing'] = []
        if result['member'] and result['member']['leader']:
            for p in api.PRESENCE.values():
                target = p['char_id']
                if together(cid,target) and not rp.membership(db,target):
                    row = db.execute('SELECT name,surname FROM characters WHERE id=?',(target,)).fetchone()
                    if row:
                        result['nearby'].append(dict(server_id=p['server_id'],char_id=target,name=row['name']+' '+row['surname']))
            result['outgoing'] = [dict(r) for r in db.execute('''SELECT i.id,i.expires,i.char_id,
              c.name||' '||c.surname AS name FROM pn_faction_invites i JOIN characters c ON c.id=i.char_id
              WHERE i.faction_id=? AND i.expires>?''',(result['member']['faction_id'],time.time()))]
        return result

    def action(db, action, uid, cid, v, p, state, presences, releases):
        if action not in ('invite','accept','decline','revoke'):
            return old_action(db,action,uid,cid,v,p,state,presences,releases)
        now=time.time()
        db.execute('DELETE FROM pn_faction_invites WHERE expires<=?',(now,))
        db.execute('DELETE FROM pn_inviter69 WHERE invite NOT IN (SELECT id FROM pn_faction_invites)')
        if action == 'invite':
            m=rp.lead(db,cid)
            sid=rp.integer(v.get('server_id'))
            target=api.world.resolve_player_id(sid,presences)
            if not together(cid,target):
                raise ValueError('Davet için iki oyuncu aynı yerde, yaya ve en fazla 5 metre uzakta olmalı.')
            if rp.membership(db,target):
                raise ValueError('Oyuncu zaten bir birlikte.')
            existing=db.execute('SELECT id FROM pn_faction_invites WHERE char_id=? AND faction_id=?',(target,m['faction_id'])).fetchone()
            if existing:
                raise ValueError('Bu oyuncunun bekleyen daveti var. Önce yanıtlamasını bekle veya daveti geri çek.')
            count=db.execute('SELECT count(*) FROM pn_faction_members WHERE faction_id=?',(m['faction_id'],)).fetchone()[0]
            pending=db.execute('SELECT count(*) FROM pn_faction_invites WHERE faction_id=?',(m['faction_id'],)).fetchone()[0]
            if pending>=20 or count+pending>=m['level']*10:
                raise ValueError('Birlik üye ve bekleyen davet sınırına ulaştı.')
            iid=secrets.token_urlsafe(18)
            db.execute('INSERT INTO pn_faction_invites VALUES(?,?,?,?)',(iid,m['faction_id'],target,now+300))
            db.execute('INSERT INTO pn_inviter69 VALUES(?,?)',(iid,cid))
        else:
            invite=db.execute('SELECT * FROM pn_faction_invites WHERE id=?',(str(v.get('invite','')),)).fetchone()
            if not invite:
                raise ValueError('Davet bulunamadı veya süresi doldu.')
            if action=='revoke':
                m=rp.lead(db,cid)
                if m['faction_id']!=invite['faction_id']:
                    raise ValueError('Bu davet senin birliğine ait değil.')
            elif invite['char_id']!=cid:
                raise ValueError('Bu davet sana ait değil.')
            elif action=='accept':
                source=db.execute('SELECT char_id FROM pn_inviter69 WHERE invite=?',(invite['id'],)).fetchone()
                leader=rp.membership(db,source['char_id']) if source else None
                if not leader or not leader['leader'] or leader['faction_id']!=invite['faction_id']:
                    raise ValueError('Davet edenin yetkisi değişmiş. Yeni bir davet iste.')
                if not together(cid,source['char_id']):
                    raise ValueError('Daveti kabul etmek için davet edenin 5 metre yakınına yaya gel.')
                return old_action(db,action,uid,cid,v,p,state,presences,releases)
            db.execute('DELETE FROM pn_faction_invites WHERE id=?',(invite['id'],))
            db.execute('DELETE FROM pn_inviter69 WHERE invite=?',(invite['id'],))
        api.world.audit(db,uid,'faction-'+action,dict(char_id=cid))
        return dict(faction=view(db,cid),on_duty=bool(p.get('faction_duty')),notice={'invite':'Birlik daveti gönderildi. 5 dakika geçerli.','decline':'Davet reddedildi.','revoke':'Davet geri çekildi.'}[action])

    def dispatch(path,uid,token,values,p,state,presences):
        if not path.startswith(('/api/factions/','/api/jobs/')) or path.endswith(('/list','/status')):
            return old_dispatch(path,uid,token,values,p,state,presences)
        # Keep DB receipts, membership, inventory and in-memory side effects atomic.
        objects=[*presences.values(),state,api.world.SEATS,api.world.VEHICLE_CACHE,api.world.SAVED_AT]
        snapshots=[copy.deepcopy(x) for x in objects]
        try:
            with api.database() as db:
                if not db.in_transaction:db.execute('BEGIN IMMEDIATE')
                return old_dispatch(path,uid,token,values,p,state,presences)
        except BaseException:
            for obj,saved in zip(objects,snapshots):obj.clear();obj.update(saved)
            raise

    rp.faction_view=view;rp.faction_action=action;rp.dispatch=dispatch
    api.factions69_installed=True
    return api
