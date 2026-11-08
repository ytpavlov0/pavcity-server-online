"""Original shared venue adapter. No third-party runtime, grants or DB changes.

UwU is an exterior meeting point. The linked job script does not contain its
Gabz interior, so this adapter never fabricates a door/interior transition.
"""
import copy, math, time

CAFE = dict(id=17901,kind='cafe',name='UwU · Sosyal buluşma',x=-592.01,y=-1057.79,z=22.34,radius=7,icon='cat',color='#f0a9d5',exterior=True)
DESCRIPTION = 'Dış buluşma noktası. Yakın sohbet ve sesli konuşmayla sosyalleş. Gabz kafe interiorü bu pakette bulunmuyor.'

def install(api):
    if getattr(api,'community179_installed',False):return api
    original=api.dispatch
    def dispatch(path,payload,token):
        command=str(payload.get('message','')).strip().split(' ',1)[0].lower()
        ours=path.startswith('/api/community179/') or path=='/api/chat/send' and command in ('/uwu','/mekanlar') or path=='/api/services/open' and payload.get('kind')=='cafe'
        with api.LOCK:
            if ours:
                checked,cookie=original('/api/auth/me',{},token)
                if not checked.get('success'):return checked,cookie
                p=api.PRESENCE.get(token);s=api.GTA_STATE.get(token)
                if not p or not s or p.get('world')!='gta' or time.time()-s.get('last_seen',0)>30:raise ValueError('Önce şehre bağlan.')
                if path=='/api/community179/list':return dict(success=True,venues=[dict(CAFE)]),None
                if path=='/api/chat/send':return dict(success=True,info=dict(title='Sosyal buluşma noktaları',headers=['Mekan','Konum','Durum'],rows=[[CAFE['name'],f"{CAFE['x']}, {CAFE['y']}",'Dış buluşma noktası']]),notice='/uwu · Haritadan kafe hedefini seçebilirsin.'),None
                if path not in ('/api/community179/open','/api/services/open'):raise ValueError('Bilinmeyen mekan işlemi.')
                if p.get('dimension',0)!=0 or p.get('health',0)<=100 or s.get('vehicle_id') or math.dist([s[k]for k in ('x','y','z')],[CAFE[k]for k in ('x','y','z')])>7:raise ValueError('UwU buluşma noktasına yaya olarak 7 metre yaklaş.')
                return dict(success=True,service=dict(CAFE),description=DESCRIPTION),None
            result,cookie=original(path,payload,token)
            if path=='/api/gta/sync' and result.get('success'):
                result=dict(result,services=[*result.get('services',[]),dict(CAFE)],community179=dict(venues=[dict(CAFE)]))
            return result,cookie
    api.dispatch=dispatch;api.community179_installed=True
    return api
