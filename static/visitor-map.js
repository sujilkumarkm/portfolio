(() => {
  const root = document.querySelector('#visitor-map');
  const svg = document.querySelector('#world-map');
  const status = document.querySelector('#map-status');
  const selection = document.querySelector('#map-selection');
  const table = document.querySelector('#map-country-table tbody');
  const ns = 'http://www.w3.org/2000/svg';
  const countries = new Map();
  let counts = new Map(), selected, loading = false;
  const listURL = code => root.dataset.list + '?country__exact=' + encodeURIComponent(code);
  function describe(code, name) {
    const row = counts.get(code) || {visitors: 0, visits: 0};
    selection.replaceChildren(document.createTextNode(`${name}: ${row.visitors} unique visitors · ${row.visits} visits. `));
    const link = document.createElement('a'); link.href = listURL(code); link.textContent = 'View visitors →'; selection.append(link);
    selected = [code, name];
  }
  async function refresh() {
    if (loading) return; loading = true;
    try {
      const response = await fetch(root.dataset.counts, {cache: 'no-store', headers: {'Accept': 'application/json'}});
      if (!response.ok || !response.headers.get('content-type')?.includes('application/json')) throw Error();
      const data = await response.json(); counts = new Map(data.countries.map(r => [r.country, r]));
      const max = Math.max(1, ...data.countries.map(r => r.visitors));
      for (const [code, item] of countries) {
        const count = counts.get(code)?.visitors || 0;
        item.path.style.fill = count ? `hsl(27 95% ${65 - 22 * Math.log1p(count)/Math.log1p(max)}%)` : 'var(--map-empty)';
        const label = `${item.name}: ${count} unique visitors`;
        item.path.setAttribute('aria-label', label); item.title.textContent = label;
      }
      table.replaceChildren();
      for (const row of [...data.countries].sort((a,b) => b.visitors-a.visitors)) {
        const tr = document.createElement('tr'), td = document.createElement('td'), link = document.createElement('a');
        link.href = listURL(row.country); link.textContent = countries.get(row.country)?.name || row.country || 'Unknown'; td.append(link); tr.append(td);
        for (const value of [row.visitors,row.visits]) { const cell=document.createElement('td'); cell.textContent=value; tr.append(cell); }
        table.append(tr);
      }
      document.querySelector('#map-total').textContent = `${data.countries.reduce((n,r)=>n+r.visitors,0)} unique visitors · ${data.countries.reduce((n,r)=>n+r.visits,0)} visits`;
      if (selected) describe(...selected);
      status.textContent = 'Updated ' + new Date().toLocaleTimeString();
    } catch (_) { status.textContent = 'Unable to refresh. Please retry or sign in again.'; }
    finally { loading = false; }
  }
  async function start() {
    try {
      const response = await fetch(root.dataset.outlines); if (!response.ok) throw Error();
      const world = await response.json();
      for (const feature of world.features) {
        const {code, name} = feature.properties;
        const polygons = feature.geometry.type === 'Polygon' ? [feature.geometry.coordinates] : feature.geometry.coordinates;
        const path = document.createElementNS(ns,'path');
        path.setAttribute('d', polygons.map(polygon => polygon.map(ring => ring.map(([lon,lat],i) => `${i?'L':'M'}${((lon+180)/360*1000).toFixed(2)},${((90-lat)/180*500).toFixed(2)}`).join(' ')+'Z').join(' ')).join(' '));
        path.setAttribute('tabindex','0'); path.setAttribute('role','button');
        const title = document.createElementNS(ns,'title'); path.append(title); svg.append(path);
        countries.set(code,{path,title,name});
        path.addEventListener('pointerenter',()=>describe(code,name)); path.addEventListener('focus',()=>describe(code,name));
        path.addEventListener('click',()=>describe(code,name));
        path.addEventListener('keydown',e=>{ if(e.key==='Enter') location.href=listURL(code); if(e.key===' ') { e.preventDefault(); describe(code,name); } });
      }
      await refresh(); setInterval(()=>{if(!document.hidden) refresh();},15000);
    } catch (_) { status.textContent='Map unavailable. Use the visitor details list.'; }
  }
  document.querySelector('#map-refresh').addEventListener('click',refresh);
  start();
})();
