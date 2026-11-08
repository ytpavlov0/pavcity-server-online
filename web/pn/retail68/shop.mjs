// Shared purchase UI for PC and mobile. Retry IDs survive a lost response.
const pending = new Map();
const money = value => '$' + Number(value).toLocaleString('tr-TR');
export function purchase(request, catalog, item, qty, storage) {
  if (!Number.isInteger(qty) || qty < 1 || qty > (item.key === 'phone' ? 1 : 10)) throw Error('Geçerli adet seç.');
  const shop = catalog.property_shop68;
  const body = {kind: catalog.kind, item: item.key, qty, property_id: shop?.id || 0, property_version: shop?.version || 0};
  const key = 'pav-shop68:' + JSON.stringify([catalog.buyer68, body]);
  let id = pending.get(key);
  try { if (storage === undefined) storage = globalThis.sessionStorage; } catch {}
  try { id ||= storage?.getItem(key); } catch {}
  id ||= crypto.randomUUID();
  pending.set(key, id);
  try { storage?.setItem(key, id); } catch {}
  let running;
  return () => {
    if (running) return running;
    running = request('/api/shops/buy', {...body, request_id: id}).then(value => {
      if (!value.success) throw Error(value.error || 'Alışveriş tamamlanamadı.');
      pending.delete(key);
      try { storage?.removeItem(key); } catch {}
      return value;
    }).finally(() => { running = null; });
    return running;
  };
}

export async function mountShop({root, request, onResult = () => {}, kind = 'market'}) {
  const el = (tag, text) => {const n = document.createElement(tag); if (text !== undefined) n.textContent = text; return n;};
  const message = el('p', 'Ürünler yükleniyor…');
  message.setAttribute('role', 'status'); root.append(message);
  const data = await request('/api/shops/list', {kind});
  if (!data.success) throw Error(data.error || 'Market açılamadı.');
  if (!root.isConnected) return;
  const content = el('div'); content.className = 'rp-shop-grid';
  const balance = el('p', 'Nakit ' + money(data.money));
  const search = el('input'); search.type = 'search'; search.placeholder = 'Ürün ara'; search.setAttribute('aria-label', 'Ürün ara');
  search.oninput = () => {const term = search.value.toLocaleLowerCase('tr'); for (const card of content.children) card.hidden = !card.dataset.name.includes(term);};
  root.replaceChildren(el('h3', data.property_shop68?.name || (kind === 'electronics' ? 'Digital Den' : 'Market')), balance, search, content, message);
  message.textContent = data.property_shop68 ? 'Bu alışveriş bulunduğun markete bağlıdır.' : 'Satın almadan önce toplam tutarı onayla.';
  for (const item of data.items) {
    const row = el('article'); row.className = 'item';
    row.dataset.name = item.name.toLocaleLowerCase('tr');
    const label = el('label', 'Adet '), qty = el('input');
    Object.assign(qty, {type: 'number', min: '1', max: item.key === 'phone' ? '1' : '10', step: '1', value: '1'});
    label.append(qty);
    const review = el('button', 'Satın al'), confirm = el('button', 'Alımı onayla'), cancel = el('button', 'Vazgeç'), total = el('p');
    for (const b of [review, confirm, cancel]) b.type = 'button';
    confirm.hidden = cancel.hidden = true;
    let send, busy = false;
    const reset = () => {send = null; qty.disabled = false; review.hidden = false; confirm.hidden = cancel.hidden = true; total.textContent = '';};
    review.onclick = () => {
      try {
        const count = Number(qty.value);
        // Allocate only when the player confirms; changing a review cannot buy.
        if (!Number.isInteger(count) || count < 1 || count > Number(qty.max)) throw Error('Geçerli adet seç.');
        send = () => purchase(request, data, item, count)();
        qty.disabled = true; review.hidden = true; confirm.hidden = cancel.hidden = false;
        total.textContent = `${count} adet ${item.name} · Toplam ${money(item.price * count)}`;
      } catch (e) { message.textContent = e.message; }
    };
    cancel.onclick = () => {if (!busy) reset();};
    confirm.onclick = async () => {
      if (busy || !send) return;
      busy = true; confirm.disabled = cancel.disabled = true;
      try {
        const result = await send();
        reset();
        await onResult(result);
        if (!root.isConnected) return;
        balance.textContent = 'Nakit ' + money(result.money);
        message.textContent = result.notice; reset();
      } catch (e) {if (root.isConnected) message.textContent = e.message;}
      finally {busy = false; confirm.disabled = cancel.disabled = false;}
    };
    row.append(el('h4', item.name), el('p', `${money(item.price)} · ${item.kg} kg`), label, review, total, confirm, cancel);
    if (typeof item.image === 'string' && item.image.startsWith('/pn/')) {
      const image = el('img'); image.src = item.image; image.alt = item.name; image.loading = 'lazy'; image.className = 'rp-item-image'; row.append(image);
    }
    content.append(row);
  }
}
