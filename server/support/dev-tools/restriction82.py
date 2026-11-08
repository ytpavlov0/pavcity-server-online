"""Use the same persisted restraints as the existing casino services."""
def free_actor(api,p,now):
 if p.get('cuffed')or p.get('restrained')or p.get('inventory_action'):raise ValueError('Bu işlem için serbest olmalısın.')
 if getattr(api,'services178_installed',False):
  with api.database()as db:r=db.execute('SELECT cuffed,prone FROM pn_restrictions178 WHERE char_id=? AND life=? AND dimension=? AND until>?',(p['char_id'],p.get('life_id',0),p.get('dimension',0),now)).fetchone()
  if r and(r['cuffed']or r['prone']):raise ValueError('Kısıtlıyken bu işlem kullanılamaz.')
