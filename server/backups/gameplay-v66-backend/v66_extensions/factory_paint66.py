"""Stable stock paint before the first driver. Saved and addon paint wins."""
def install(api,document):
 if getattr(api,'factory_paint66_installed',False):return api
 if document.get('version')!=66 or not isinstance(document.get('models'),dict):raise ValueError('Factory palette66 catalogue')
 palettes={}
 for model,row in document['models'].items():
  choices=row.get('palettes')
  if not isinstance(model,str)or not model or not isinstance(choices,list)or not 1<=len(choices)<=128:raise ValueError('Factory palette66 model')
  if any(not isinstance(c,dict)or any(type(c.get(k))is not int or not 0<=c[k]<=160 for k in('primary','secondary'))for c in choices):raise ValueError('Factory palette66 indices')
  palettes[model]=tuple(dict(c)for c in choices)
 previous=api.world.public
 def public(row):
  result=previous(row);choices=palettes.get(result.get('model'));vid=result.get('id')
  if not choices or type(vid)is not int or vid<1:return result
  defaults=choices[((vid*2654435761)&0xffffffff)%len(choices)];mods=dict(result.get('mods')or{});sides=[]
  for side in('primary','secondary'):
   if side not in mods and side+'_rgb'not in mods:mods[side]=defaults[side];sides.append(side)
  return dict(result,mods=mods,factory_paint66=dict(presentation_only=True,default_sides=sides))if sides else result
 api.world.public=public;api.factory_paint66_installed=True
 return api
