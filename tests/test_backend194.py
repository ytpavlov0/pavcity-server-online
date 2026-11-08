"""194: the NPC ambulance call (5 s after going down), shared within 400 m in sync, NPC revive once the call is 18 s
old; without a call the 192 medic minute stands; the hospital still waits the minute."""
from pathlib import Path
import sys,tempfile,time,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT),str(ROOT/'support/dev-tools'),str(ROOT/'backups/gameplay-v29-backend')]
import online_engine
tmp=tempfile.TemporaryDirectory(prefix='v194-');online_engine.DB_PATH=str(Path(tmp.name)/'fixture.db');online_engine.init_db()
from gameplay_v29 import session_api as api
from gameplay_mobile170 import install as mobile170
mobile170(api)
import crime192,run_gameplay_live_v194 as v194
crime192.install(api);v194.wrap(api)
def player(tag,dx=0):
 data,token=api.dispatch('/api/auth/register',dict(username='t194'+tag+str(time.time_ns()),password='fixture-194-pass'),'')
 cid=api.dispatch('/api/character/create',dict(name='Deniz',surname='Deneme'+''.join(chr(97+int(c))for c in str(time.time_ns())[-8:]),country='tr'),token)[0]['character']['id']
 with api.database()as db:db.execute('UPDATE pn_wallet SET balance=1000 WHERE user_id=?',(data['user_id'],))
 r=api.dispatch('/api/gta/join',dict(char_id=cid),token)[0]
 sp={k:r['spawn'][k]for k in('x','y','z')};sp['x']+=dx
 return token,sp
def sync(token,sp,health=200):return api.dispatch('/api/gta/sync',{**sp,'heading':0,'health':health,'life_id':api.PRESENCE[token].get('life_id',0),'separate_voice':True},token)[0]
class Ems194(unittest.TestCase):
 def test_call_shared_and_revive_after_arrival(self):
  tv,sv=player('v');tn,sn=player('n',50);tf,sf=player('f',900)
  for t,s in((tv,sv),(tn,sn),(tf,sf)):sync(t,s)
  p=api.PRESENCE[tv];p['health']=100;p['dead_at']=time.time()-2;api.GTA_STATE[tv]['health']=100
  self.assertFalse(api.dispatch('/api/gta/ems194',{},tv)[0]['success'],'2 s: too early')
  self.assertFalse(api.dispatch('/api/gta/npcrevive192',{},tv)[0]['success'],'no call, medic minute')
  p['dead_at']=time.time()-6;r=api.dispatch('/api/gta/ems194',{},tv)[0];self.assertTrue(r['success'],r)
  again=api.dispatch('/api/gta/ems194',{},tv)[0];self.assertEqual(again['ems194']['id'],r['ems194']['id'],'one call per death')
  self.assertTrue(sync(tv,sv,100)['ems194'][0]['me'])
  near=sync(tn,sn).get('ems194');self.assertTrue(near and near[0]['id']==r['ems194']['id']and not near[0]['me'],near)
  self.assertNotIn('ems194',sync(tf,sf),'900 m away: not shown')
  self.assertFalse(api.dispatch('/api/gta/respawn',{'life_id':p.get('life_id',0)},tv)[0]['success'],'hospital waits')
  q=api.dispatch('/api/gta/npcrevive192',{},tv)[0];self.assertFalse(q['success']);self.assertIn('Ambulans yolda',q['error'])
  v194.STATE['calls'][p['char_id']]['t']-=19
  q=api.dispatch('/api/gta/npcrevive192',{},tv)[0];self.assertTrue(q['success'],q);self.assertEqual(p['health'],120)
  self.assertNotIn('ems194',sync(tn,sn),'call over after the revive')
 def test_call_ends_on_new_death(self):
  tv,sv=player('d');sync(tv,sv);p=api.PRESENCE[tv];p['health']=100;p['dead_at']=time.time()-7;api.GTA_STATE[tv]['health']=100
  self.assertTrue(api.dispatch('/api/gta/ems194',{},tv)[0]['success'])
  p['dead_at']=time.time()-1
  self.assertNotIn('ems194',sync(tv,sv,100))
if __name__=='__main__':unittest.main()
