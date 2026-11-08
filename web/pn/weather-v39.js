/* Shared fictional city clock/weather. One small timer per active HUD. */
(()=>{'use strict';
 const names={EXTRASUNNY:'Güneşli',CLEAR:'Açık',CLOUDS:'Bulutlu',SMOG:'Puslu',FOGGY:'Sisli',OVERCAST:'Kapalı',RAIN:'Yağmurlu',THUNDER:'Fırtına',CLEARING:'Açılıyor',NEUTRAL:'Ilıman',SNOW:'Karlı',BLIZZARD:'Tipi',SNOWLIGHT:'Hafif kar',XMAS:'Karlı'};
 const paths={sun:'M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10M12 1v3M12 20v3M1 12h3M20 12h3M4 4l2 2M18 18l2 2M4 20l2-2M18 6l2-2',cloud:'M5 18h13a4 4 0 0 0 0-8 6 6 0 0 0-11-2 5 5 0 0 0-2 10Z',rain:'M4 14h14a4 4 0 0 0 0-8A6 6 0 0 0 7 4a5 5 0 0 0-3 10ZM7 17l-1 4M13 17l-1 4M19 17l-1 4'};
 addEventListener('pav-game-created',({detail:game})=>{
  const radar=game.hud.querySelector('.pn-radar-frame');if(!radar||radar.querySelector('.pav-weather39'))return;
  const box=document.createElement('div');box.className='pav-weather39';box.hidden=true;box.setAttribute('aria-label','Şehir saati ve hava durumu');box.innerHTML='<time></time><svg viewBox="0 0 24 24" aria-hidden="true"><path/></svg><span></span>';radar.append(box);
  const clock=box.querySelector('time'),label=box.querySelector('span'),icon=box.querySelector('path');let environment=null,received=0,lastClock='',timer;
  const dispose=()=>{clearInterval(timer);removeEventListener('pav-game-data',receive);box.remove();};
  const tick=()=>{
   if(!game.hud.isConnected){dispose();return;}if(!environment||document.hidden)return;
   const total=((environment.hour*3600+environment.minute*60+(environment.second||0)+Math.max(0,performance.now()-received)/1000*environment.rate)%86400+86400)%86400;
   const text=String(Math.floor(total/3600)).padStart(2,'0')+':'+String(Math.floor(total/60)%60).padStart(2,'0');
   if(text!==lastClock){lastClock=text;clock.textContent=text;clock.dateTime=text;}
  };
  const receive=({detail})=>{
   const env=detail.environment;if(!env||![env.hour,env.minute,env.second??0].every(Number.isFinite))return;
   environment={...env,rate:Number.isFinite(env.rate)&&env.rate>0&&env.rate<=120?env.rate:30};received=performance.now();
   label.textContent=names[env.weather]||'Hava';icon.setAttribute('d',paths[/RAIN|THUNDER|SNOW|BLIZZARD|XMAS/.test(env.weather)?'rain':/CLOUDS|SMOG|FOGGY|OVERCAST|CLEARING/.test(env.weather)?'cloud':'sun']);
   box.title=(env.weather_region||'Los Santos')+' · '+label.textContent;box.hidden=false;tick();
  };
  addEventListener('pav-game-data',receive);timer=setInterval(tick,1000);
 });
})();
