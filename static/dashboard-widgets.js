(() => {
  const grid = document.querySelector('.dashboard-widgets');
  if (!grid) return;
  const key = grid.dataset.layoutKey;
  let saved = [];
  try { saved = JSON.parse(localStorage.getItem(key) || '[]'); } catch (_) {}
  if (!Array.isArray(saved)) saved = [];
  const widgets = [...grid.children];
  for (const item of saved) {
    const widget = widgets.find(w => w.dataset.widget === item.id);
    if (!widget) continue;
    grid.append(widget);
    if (item.width > 220 && item.width < 2000) widget.style.width = `${item.width}px`;
    if (item.height > 100 && item.height < 2000) widget.style.height = `${item.height}px`;
  }
  const save = () => {
    try { localStorage.setItem(key, JSON.stringify([...grid.children].map(w => ({id: w.dataset.widget, width: w.offsetWidth, height: w.offsetHeight})))); } catch (_) {}
  };
  let dragged;
  for (const widget of widgets) {
    const handle = document.createElement('button');
    handle.type = 'button'; handle.className = 'widget-handle'; handle.textContent = 'Move widget';
    handle.draggable = true;
    handle.title = 'Drag to reorder, or use Left and Right arrow keys';
    widget.prepend(handle);
    handle.addEventListener('dragstart', e => { dragged = widget; e.dataTransfer.setData('text/plain', widget.dataset.widget); });
    handle.addEventListener('dragend', () => { dragged = null; save(); });
    handle.addEventListener('keydown', e => {
      if (e.key === 'ArrowLeft' && widget.previousElementSibling) { grid.insertBefore(widget, widget.previousElementSibling); e.preventDefault(); }
      if (e.key === 'ArrowRight' && widget.nextElementSibling) { grid.insertBefore(widget.nextElementSibling, widget); e.preventDefault(); }
      handle.focus(); save();
    });
    widget.addEventListener('dragover', e => { if (dragged) e.preventDefault(); });
    widget.addEventListener('drop', e => { e.preventDefault(); if (dragged && dragged !== widget) grid.insertBefore(dragged, widget); save(); });
    widget.addEventListener('pointerup', save);
    new ResizeObserver(save).observe(widget);
  }
  document.querySelector('#reset-layout').addEventListener('click', () => {
    try { localStorage.removeItem(key); } catch (_) {}
    location.reload();
  });
})();
