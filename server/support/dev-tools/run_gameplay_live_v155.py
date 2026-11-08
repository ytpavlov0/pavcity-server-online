"""155 backend: 154 with two protection fixes from its first minutes live.

- Rejections of the per-IP stream cap no longer count toward the 10-minute ban: a legitimate player's io-worker opens
  up to 32 prefetch streams, collected 400 cap rejections within a minute and was banned (protection154.log).
- The per-IP stream cap (4) applies only while the global data slots are contended (active >= slots-2); a player
  alone on the server may use every slot, so loading is not throttled when nothing competes.
- PAV154_BAN_AFTER overrides the ban threshold (tests). Shared state and stats stay in run_gameplay_live_v154."""
from pathlib import Path
import sys,os,time,random
from urllib.parse import urlsplit
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'support/dev-tools'))
import run_gameplay_live_v154 as previous
host=previous.host
install=previous.install
P=previous;SLOTS=previous.previous.SLOTS;BAN_AFTER=max(1,int(os.environ.get('PAV154_BAN_AFTER',P.BAN_AFTER)))
class Handler(previous.Handler):
 def _guard(self,p):
  ip=self.headers.get('Cf-Connecting-Ip')or(self.headers.get('X-Forwarded-For')or'').split(',')[0].strip()
  if not ip:return True,None
  country=(self.headers.get('Cf-Ipcountry')or'').upper();now=time.time();kind=P.classify(p)
  with P.LOCK:
   P.purge(now);P.STATS['requests']+=1;P.seen[ip]=now
   if country:P.COUNTRIES[country]+=1
   until=P.banned.get(ip)
   if until and until>now:P.STATS['banned_requests']+=1;self._reject(403,body=b'Too many requests. Try again in a few minutes.');return False,None
   allow=P.geo_allow(now)
   if allow and country and country not in allow:
    P.STATS['geo_blocked']+=1;P.STATS['geo_'+country]+=1;P.note('geo',ip,country,now);self._reject(403,body=P.GEO_PAGE,ctype='text/html; charset=utf-8');return False,None
   window,limit=P.LIMITS[kind];q=P.hits[ip,kind]
   while q and q[0]<now-window:q.popleft()
   over=len(q)>=limit;reason=kind
   if not over and kind=='data'and P.active.get(ip,0)>=P.DATA_PER_IP and sum(P.active.values())>=max(1,SLOTS-2):over=True;reason='data_streams'
   if over:
    P.STATS['limited_'+reason]+=1
    if reason!='data_streams':
     rj=P.rejects[ip]
     while rj and rj[0]<now-60:rj.popleft()
     rj.append(now)
     if len(rj)>=BAN_AFTER:P.banned[ip]=now+P.BAN_SECONDS;P.STATS['bans']+=1;rj.clear();P.note('ban',ip,country,now)
    self._reject(429,retry=P.RETRY.get(kind)or random.randint(1,3));return False,None
   q.append(now)
   if kind!='data':return True,None
   P.active[ip]=P.active.get(ip,0)+1
  def done():
   with P.LOCK:
    n=P.active.get(ip,1)-1
    if n<=0:P.active.pop(ip,None)
    else:P.active[ip]=n
  return True,done
 def do_GET(self):
  if urlsplit(self.path).path=='/pn/server-capabilities-v155.json':
   now=time.time()
   with P.LOCK:
    prot=dict(P.STATS);prot.update(unique_ips_3min=len(P.seen),active_data_ips=len(P.active),banned_now=sum(1 for t in P.banned.values()if t>now),countries=dict(P.COUNTRIES.most_common(15)),geo_allow=sorted(P.geo_allow(now)),limits={k:dict(window_s=w,max=m)for k,(w,m)in P.LIMITS.items()},data_streams_per_ip=P.DATA_PER_IP,contention_from=max(1,SLOTS-2),ban_after=BAN_AFTER,ban_seconds=P.BAN_SECONDS,stream_rejections_ban=False)
   return self.json51(200,dict(backend_release='v155',base_release='v154',wasm_gzip=P.WASM_GZ.is_file(),protection=prot,pool_workers=192,data_slots=SLOTS,data_stats=dict(previous.previous.STATS),localhost_only=True,staff_interiors=True,sync_one_connection=True,club_npcs=True,afk_zone=True))
  return super().do_GET()
if __name__=='__main__':
 p=__import__('argparse').ArgumentParser();p.add_argument('--port',type=int,default=8018);p.add_argument('--live',action='store_true');p.add_argument('--fixture-db');args=p.parse_args()
 if args.port==8000 and not args.live:p.error('Production requires --live')
 if args.fixture_db:
  f=Path(args.fixture_db).resolve()
  if R/'backups'not in f.parents or not f.name.endswith('-v155.db'):p.error('Disposable -v155.db under backups required')
  host.online_engine.DB_PATH=str(f)
  m=previous
  while not hasattr(m,'crash98'):m=m.previous
  m.crash98.OUTPUT=f.parent/'fixture-crashes155.jsonl'
 elif not args.live:p.error('Fixture DB required')
 host.online_engine.init_db();install();host.StableWorkerHTTPServer(('127.0.0.1',args.port),Handler,max_workers=192,pending_requests=512).serve_forever()
