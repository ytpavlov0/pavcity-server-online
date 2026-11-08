"""Presentation defaults from original addon factory palettes. No startup writes."""
MODELS={'pavtofas','pavbus','g65','audquattros','i8','skyline'}
def install(api,document):
 if getattr(api,'factory_paint50_installed',False):return api
 models=document.get('models')
 if not isinstance(models,dict)or set(models)!=MODELS:raise ValueError('Factory palette catalogue mismatch')
 palettes={}
 for name,source in models.items():
  choices=source.get('palettes')
  if not isinstance(choices,list)or not 1<=len(choices)<=64:raise ValueError('Invalid factory palette count')
  for choice in choices:
   if not isinstance(choice,dict)or any(type(choice.get(k))is not int or not 0<=choice[k]<=160 for k in('primary','secondary')):raise ValueError('Invalid factory palette')
  palettes[name]=tuple(dict(v)for v in choices)
 public=api.world.public
 def view(row):
  result=public(row);choices=palettes.get(result.get('model'))
  if not choices:return result
  vid=result.get('id')
  if type(vid)is not int or vid<1:return result
  palette=choices[((vid*2654435761)&0xffffffff)%len(choices)];mods=dict(result.get('mods')or{})
  defaults=[]
  for side in('primary','secondary'):
   if side not in mods and side+'_rgb'not in mods:mods[side]=palette[side];defaults.append(side)
  if not defaults:return result
  return dict(result,mods=mods,factory_paint50=dict(presentation_only=True,default_sides=defaults))
 api.world.public=view;api.factory_paint50_installed=True;return api
