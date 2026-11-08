/* Existing authenticated game API and panel lifecycle; no extra render loop. */
addEventListener('pav-game-created', ({detail:game}) => queueMicrotask(() => {
  game.market = async () => {
    const panel = game.openRP('Market · Alışveriş', '<div data-shop68></div>', 'rp-market');
    try {
      const {mountShop} = await import('/pn/retail68/shop.mjs');
      const root = panel.querySelector('[data-shop68]');
      if (!root?.isConnected) return;
      await mountShop({root, request:(path,body)=>game.api(path,body), onResult:r=>{game.applyLoadout(r.loadout); game.notice(r.notice);}});
    } catch (e) { if (panel.isConnected) panel.querySelector('.rp-error').textContent = e.message; }
  };
  const original = game.openService;
  if (original) game.openService = function(kind, ...args) {return kind === 'market' ? game.market() : original.call(this, kind, ...args);};
}));
