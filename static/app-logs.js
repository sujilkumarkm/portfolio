(() => {
  const panel = document.querySelector('.logs-panel');
  if (!panel) return;
  const output = document.getElementById('logs-output');
  const status = document.getElementById('logs-status');
  const live = document.getElementById('logs-live');
  let busy = false, timer;
  async function refresh() {
    if (busy) return;
    busy = true;
    const params = new URLSearchParams({level: document.getElementById('logs-level').value, category: document.getElementById('logs-category').value, q: document.getElementById('logs-search').value});
    try {
      const response = await fetch(`${panel.dataset.url}?${params}`, {credentials:'same-origin', headers:{Accept:'application/json'}});
      if (!response.ok || response.redirected) throw new Error('Unable to read logs. Check your login and refresh.');
      const data = await response.json();
      const follow = output.scrollHeight - output.scrollTop - output.clientHeight < 50 || !output.textContent;
      output.textContent = data.lines.length ? data.lines.join('\n') : 'No events match these filters yet.';
      if (follow) output.scrollTop = output.scrollHeight;
      status.textContent = `${data.lines.length} events · ${live.checked ? 'Live' : 'Paused'}`;
    } catch (error) {status.textContent = error.message || 'Could not load logs.';}
    finally {busy = false;}
  }
  document.getElementById('logs-refresh').addEventListener('click', refresh);
  ['logs-level','logs-category','logs-live'].forEach(id => document.getElementById(id).addEventListener('change', refresh));
  document.getElementById('logs-search').addEventListener('input', () => {clearTimeout(timer); timer = setTimeout(refresh, 300);});
  setInterval(() => {if (live.checked && !document.hidden) refresh();}, 5000);
  refresh();
})();
