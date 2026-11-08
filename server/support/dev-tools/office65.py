"""Install versioned office policies before the existing backend chain is built."""
from pathlib import Path
import importlib,importlib.util,sys,json,hashlib
R=Path(__file__).resolve().parents[2];D=R/'backups/gameplay-v65-backend/v65_extensions'
def configure():
 pins=json.loads((D/'office208.json').read_text());root=R/'backups/mobile-office208/public'
 for name,key in [('office/scene.json','scene_sha256'),('office/ground.bin','ground_sha256')]:
  if hashlib.sha256((root/name).read_bytes()).hexdigest()!=pins[key]:raise RuntimeError('Office208 geometry pin mismatch')
 aliases={'v33_extensions.gameplay33':'gameplay65','v45_extensions.property_transition45':'property_transition65','v48_extensions.property_preflight48':'property_preflight65','v61_extensions.property61':'property_meta65','v63_extensions.property63':'property_faction65'}
 for name,file in aliases.items():
  package=name.split('.')[0];version=package.split('_')[0];parent=R/('backups/gameplay-'+version+'-backend');sys.path.insert(0,str(parent));module=importlib.import_module(package)
  if name in sys.modules:
   if Path(sys.modules[name].__file__).resolve()!=D/(file+'.py'):raise RuntimeError('Office policy must be configured before backend install: '+name)
   continue
  spec=importlib.util.spec_from_file_location(name,D/(file+'.py'));loaded=importlib.util.module_from_spec(spec);sys.modules[name]=loaded;spec.loader.exec_module(loaded);setattr(module,name.split('.')[-1],loaded)
 return pins
