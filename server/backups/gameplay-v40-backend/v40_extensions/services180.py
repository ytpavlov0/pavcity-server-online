"""Next candidate: exterior LSPD desk, retaining the pinned 178 protocol.

Install instead of services178 on a fresh server process. No membership,
leader, wallet, equipment or teleport authority is added by this revision.
"""
from pathlib import Path
import hashlib,importlib.util

PD=dict(id=17801,kind='police',name='LSPD · Görev / teçhizat',x=434.5,y=-981.5,z=30.698741912841797,radius=3)
OLD=(441.1,-981.9,30.69)
SOURCE_SHA256='87d0c350a7153ace3a317c691de214d928f0139c5092ea5661522e503798710b'

def relocate(db):
    row=db.execute('SELECT x,y,z FROM pn_faction_duty WHERE id=?',(PD['id'],)).fetchone()
    if not row:return
    position=tuple(row)
    if not any(all(abs(a-b)<1e-5 for a,b in zip(position,expected))for expected in (OLD,tuple(PD[k]for k in ('x','y','z')))):
        raise ValueError('LSPD görev noktası özelleştirilmiş; otomatik konum geçişi uygulanmadı.')
    db.execute('UPDATE pn_faction_duty SET x=?,y=?,z=? WHERE id=?',(*(PD[k]for k in ('x','y','z')),PD['id']))

def install(api):
    if getattr(api,'services180_installed',False):return api
    if getattr(api,'services178_installed',False):
        raise ValueError('180 yerine 178 zaten kurulu; yeni süreçte yalnız services180.install kullan.')
    source=Path(__file__).with_name('services178.py')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==SOURCE_SHA256,'178 source changed; review before installing 180'
    # Refuse overwriting custom coordinates before installing any handler.
    with api.database()as db:
        if db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='pn_faction_duty'").fetchone():relocate(db)
    spec=importlib.util.spec_from_file_location('_pav_services180_core',source)
    core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core);core.PD=dict(PD)
    core.install(api)
    with api.database()as db:relocate(db)
    api.services180_installed=True
    return api
