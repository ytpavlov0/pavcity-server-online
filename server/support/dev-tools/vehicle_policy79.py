"""Traffic and dealer allowlists have different purposes. Do not mix them."""
from pathlib import Path
import importlib,importlib.util,sys
R=Path(__file__).resolve().parents[2]

def configure():
 name='v35_extensions.gameplay35';source=Path(__file__).with_name('vehicle_filter79.py')
 sys.path.insert(0,str(R/'backups/gameplay-v35-backend'))
 package=importlib.import_module('v35_extensions')
 if name in sys.modules:
  if Path(sys.modules[name].__file__).resolve()!=source:raise RuntimeError('79 vehicle policy must be configured before backend installation')
  return
 spec=importlib.util.spec_from_file_location(name,source);module=importlib.util.module_from_spec(spec)
 sys.modules[name]=module;spec.loader.exec_module(module);package.gameplay35=module
