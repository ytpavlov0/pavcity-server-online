"""Property catalog metadata. Geometry readiness remains enforced by48."""
import time
def install(api):
    if getattr(api,'property61_installed',False):return api
    previous=api.dispatch
    owners={}
    def dispatch(path,payload,token):
        result,cookie=previous(path,payload,token)
        if result.get('success') and path in ('/api/properties/list','/api/gta/sync'):
            p=api.PRESENCE.get(token);state=api.GTA_STATE.get(token)
            if p and state:
                with api.database() as db:
                    for v in result.get('properties',[]):
                        cached=owners.get(v['owner']);now=time.time()
                        if v['owner'] and (not cached or now-cached[0]>60):
                            owner=db.execute('SELECT name,surname FROM characters WHERE id=?',(v['owner'],)).fetchone()
                            cached=(now,' '.join(owner) if owner else None);owners[v['owner']]=cached
                            if len(owners)>2048:owners.pop(next(iter(owners)))
                        v['owner_name']=cached[1] if cached else None
                        v['distance']=round(sum((v[k]-state[k])**2 for k in ('x','y','z'))**.5,1)
                        v['interior_available']=v['kind'] in ('apartment','garage','office','market')
                        v['availability_note']='' if v['interior_available'] else 'Bu iç mekân paketi eksik. Giriş şu anda kullanılamıyor; mülk kaydın korunuyor.'
                if 'properties' in result:result['properties'].sort(key=lambda v:(v['distance'],v['id']))
        return result,cookie
    api.dispatch=dispatch;api.property61_installed=True
    return api
