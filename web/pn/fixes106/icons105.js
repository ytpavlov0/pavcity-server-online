/* PAVCITY icon set 105: one inline SVG sprite, 24px grid, 1.75 stroke, currentColor.
 * Usage: PAVIcons105.svg('cash') -> '<svg ...><use href="#pav105-cash"/></svg>' */
(()=>{'use strict';
const paths={
 heart:'<path d="M12 20s-7-4.4-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.6-7 10-7 10z"/>',
 armor:'<path d="M12 3 5 6v5c0 4.4 3 8.3 7 10 4-1.7 7-5.6 7-10V6z"/><path d="M12 7v10"/>',
 hunger:'<path d="M5 11h14a7 7 0 0 1-14 0z"/><path d="M4 11h16M9 7c0-1.5 1.5-1.5 1.5-3M13 7c0-1.5 1.5-1.5 1.5-3"/>',
 thirst:'<path d="M12 3.5s6 6.4 6 10.5a6 6 0 0 1-12 0c0-4.1 6-10.5 6-10.5z"/><path d="M9.5 14.5a2.5 2.5 0 0 0 2.5 2.5"/>',
 energy:'<path d="M13 2 5 13h6l-1 9 8-11h-6z"/>',
 cash:'<rect x="3" y="6" width="18" height="12" rx="2.5"/><circle cx="12" cy="12" r="2.6"/><path d="M6.5 9.5v.01M17.5 14.5v.01"/>',
 bank:'<path d="M3 9.5 12 4l9 5.5M5 10v8M9.7 10v8M14.3 10v8M19 10v8M3 20h18"/>',
 players:'<circle cx="9" cy="8.5" r="3.2"/><path d="M3.5 19a5.5 5.5 0 0 1 11 0"/><path d="M15.5 5.6a3 3 0 0 1 0 5.8M17 14.2a5.2 5.2 0 0 1 3.5 4.8"/>',
 clock:'<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5V12l3 2"/>',
 sun:'<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M4.6 4.6l1.4 1.4M18 18l1.4 1.4M2.5 12h2M19.5 12h2M4.6 19.4 6 18M18 6l1.4-1.4"/>',
 moon:'<path d="M19.5 14.5A8 8 0 0 1 9.5 4.5a8 8 0 1 0 10 10z"/>',
 cloud:'<path d="M7 18h10.5a4 4 0 0 0 .4-8A6 6 0 0 0 6.4 11 3.5 3.5 0 0 0 7 18z"/>',
 rain:'<path d="M7 15h10.5a4 4 0 0 0 .4-8A6 6 0 0 0 6.4 8 3.5 3.5 0 0 0 7 15z"/><path d="M9 18l-1 2.5M13 18l-1 2.5M17 18l-1 2.5"/>',
 storm:'<path d="M7 14h10.5a4 4 0 0 0 .4-8A6 6 0 0 0 6.4 7 3.5 3.5 0 0 0 7 14z"/><path d="m12.5 15-2 3.5h3l-2 3.5"/>',
 fog:'<path d="M4 9h16M6 13h12M4 17h16"/>',
 snow:'<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9"/>',
 compass:'<circle cx="12" cy="12" r="8.5"/><path d="m15.5 8.5-2.2 4.8-4.8 2.2 2.2-4.8z"/>',
 pin:'<path d="M12 21s6.5-6 6.5-11a6.5 6.5 0 0 0-13 0c0 5 6.5 11 6.5 11z"/><circle cx="12" cy="10" r="2.4"/>',
 ammo:'<path d="M7 9 9 4l2 5v11H7zM13 9l2-5 2 5v11h-4z"/><path d="M7 16h4M13 16h4"/>',
 gun:'<path d="M3 9h15l2 2-2 1H11l-1 2H7l-1 5H3l1.5-6.5L3 11z"/>',
 knife:'<path d="M4 20 14 10l2 2L6 22M14 10l5.5-5.5a1.4 1.4 0 0 1 2 2L16 12"/>',
 fist:'<path d="M8 10V6.5a1.5 1.5 0 0 1 3 0V10M11 9.5V5.5a1.5 1.5 0 0 1 3 0v4M14 9.5V6.5a1.5 1.5 0 0 1 3 0v6c0 4-2.5 7-6 7S5 17 5 13v-2a1.5 1.5 0 0 1 3 0"/>',
 mic:'<rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5.5 11a6.5 6.5 0 0 0 13 0M12 17.5V21"/>',
 micOff:'<path d="M15 10V6a3 3 0 0 0-5.6-1.5M9 9v2a3 3 0 0 0 4.6 2.5M18.5 11a6.5 6.5 0 0 1-1 3.4M5.5 11a6.5 6.5 0 0 0 9.8 5.6M12 17.5V21M4 4l16 16"/>',
 headset:'<path d="M4 15v-3a8 8 0 0 1 16 0v3"/><rect x="3.5" y="14" width="4" height="6" rx="1.5"/><rect x="16.5" y="14" width="4" height="6" rx="1.5"/>',
 eye:'<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12z"/><circle cx="12" cy="12" r="3"/>',
 key:'<rect x="3" y="7" width="18" height="10" rx="2.5"/><path d="M7 11h.01M11 11h.01M15 11h.01M8 14h8"/>',
 inventory:'<path d="M5 8h14l-1 12H6z"/><path d="M9 8V6a3 3 0 0 1 6 0v2"/>',
 car:'<path d="M5 16V12l2-5h10l2 5v4"/><path d="M3.5 12h17M5 16h14v2.5h-3V16M8 16v2.5H5V16"/><circle cx="8" cy="13.8" r=".6"/><circle cx="16" cy="13.8" r=".6"/>',
 jobs:'<rect x="3" y="7.5" width="18" height="12" rx="2.5"/><path d="M8.5 7.5V6a2 2 0 0 1 2-2h3a2 2 0 0 1 2 2v1.5M3 12.5h18M11 12.5v2h2v-2"/>',
 faction:'<path d="M12 3 4 6.5v5c0 4.6 3.4 8.4 8 9.5 4.6-1.1 8-4.9 8-9.5v-5z"/><path d="m9 12 2 2 4-4"/>',
 home:'<path d="M4 11 12 4l8 7v9H4z"/><path d="M10 20v-5h4v5"/>',
 phone:'<rect x="7" y="2.5" width="10" height="19" rx="2.6"/><path d="M11 18.5h2"/>',
 support:'<path d="M4 5.5h16v10H9l-5 4z"/><path d="M8.5 10.5h.01M12 10.5h.01M15.5 10.5h.01"/>',
 user:'<circle cx="12" cy="8.5" r="4"/><path d="M4.5 20.5a7.5 7.5 0 0 1 15 0"/>',
 police:'<path d="m12 2.8 2.4 1.7 2.9-.1.9 2.8 2.3 1.8-.9 2.8.9 2.8-2.3 1.8-.9 2.8-2.9-.1L12 21.2l-2.4-1.7-2.9.1-.9-2.8-2.3-1.8.9-2.8-.9-2.8 2.3-1.8.9-2.8 2.9.1z"/><path d="m12 8.5 1 2.1 2.3.3-1.7 1.6.4 2.3L12 13.7l-2 1.1.4-2.3-1.7-1.6 2.3-.3z"/>',
 map:'<path d="M3.5 6.5 9 4l6 2.5L20.5 4v13.5L15 20l-6-2.5-5.5 2.5z"/><path d="M9 4v13.5M15 6.5V20"/>',
 gps:'<path d="m21 3-7.5 18-2.2-7.3L4 11.5z"/>',
 settings:'<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.6 1.6 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.6 1.6 0 0 0-1.8-.3 1.6 1.6 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.6 1.6 0 0 0-1-1.5 1.6 1.6 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.6 1.6 0 0 0 .3-1.8 1.6 1.6 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.6 1.6 0 0 0 1.5-1 1.6 1.6 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.6 1.6 0 0 0 1.8.3H9a1.6 1.6 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.6 1.6 0 0 0 1 1.5 1.6 1.6 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.6 1.6 0 0 0-.3 1.8V9a1.6 1.6 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.6 1.6 0 0 0-1.5 1z"/>',
 play:'<path d="M7 4.5v15l12-7.5z"/>',
 close:'<path d="M6 6l12 12M18 6 6 18"/>',
 star:'<path d="m12 3.5 2.6 5.3 5.9.9-4.3 4.1 1 5.8L12 16.9l-5.2 2.7 1-5.8-4.3-4.1 5.9-.9z"/>',
 speed:'<path d="M4.5 16a8 8 0 1 1 15 0"/><path d="m12 13 3.5-4"/><circle cx="12" cy="13.5" r="1.2"/>',
 fuel:'<path d="M5 20V5.5A1.5 1.5 0 0 1 6.5 4h6A1.5 1.5 0 0 1 14 5.5V20M4 20h11M5 10h9M14 8.5l3 2v6.5a1.5 1.5 0 0 0 3 0V9l-3-3"/>',
 trophy:'<path d="M8 4h8v5a4 4 0 0 1-8 0zM8 6H5a3 3 0 0 0 3 4M16 6h3a3 3 0 0 1-3 4M12 13v4M8.5 20h7M10 17h4v3h-4z"/>',
 chevron:'<path d="m9 6 6 6-6 6"/>',
 search:'<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>'
};
const sprite='<svg xmlns="http://www.w3.org/2000/svg" aria-hidden="true" style="position:absolute;width:0;height:0;overflow:hidden">'+Object.entries(paths).map(([id,body])=>'<symbol id="pav105-'+id+'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'+body+'</symbol>').join('')+'</svg>';
const mount=()=>{if(document.getElementById('pav105-sprite'))return;const host=document.createElement('div');host.id='pav105-sprite';host.innerHTML=sprite;document.body.prepend(host);};
if(document.body)mount();else addEventListener('DOMContentLoaded',mount,{once:true});
window.PAVIcons105={names:Object.keys(paths),svg:(name,cls='')=>paths[name]?'<svg class="pav105-i '+cls+'" viewBox="0 0 24 24" aria-hidden="true"><use href="#pav105-'+name+'"/></svg>':'',weather:id=>({0:'sun',1:'sun',2:'cloud',3:'fog',4:'fog',5:'cloud',6:'rain',7:'storm',8:'cloud',9:'cloud',10:'snow',11:'snow',12:'snow',13:'snow'})[id]||'sun'};
})();
