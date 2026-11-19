(() => {
  const form = document.getElementById('learning-form');
  if (!form) return;
  const cards = document.getElementById('learning-cards');
  const status = document.getElementById('learning-status');
  const add = document.getElementById('add-idea');
  const submit = form.querySelector('[type=submit]');
  let queue = Promise.resolve(), dirty = false, finalizing = false, revision = 0;
  function values() {
    return [...cards.children].map(card => ({heading: card.querySelector('input').value, explanation: card.querySelector('textarea').value}));
  }
  function persist(action) {
    const ideas = values();
    const sentRevision = revision;
    status.textContent = action === 'save' ? 'Saving learning…' : 'Saving draft…';
    queue = queue.catch(() => {}).then(async () => {
      const response = await fetch(form.dataset.url, {method: 'POST', credentials: 'same-origin', headers: {'Content-Type': 'application/json', 'X-CSRFToken': form.querySelector('[name=csrfmiddlewaretoken]').value}, body: JSON.stringify({date: form.dataset.date, ideas, action})});
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.error || 'Could not save. Check your connection or login, then try again.');
      }
      const data = await response.json();
      if (sentRevision === revision) { dirty = false; status.textContent = data.message; }
      else { status.textContent = 'Unsaved changes'; }
      return data;
    });
    queue.catch(error => { status.textContent = error.message; dirty = true; });
    return queue;
  }
  function renderCard(idea) {
    const card = document.createElement('fieldset');
    card.className = 'learning-editor';
    const legend = document.createElement('legend');
    legend.textContent = 'Learning idea';
    const headingLabel = document.createElement('label');
    headingLabel.textContent = 'Heading';
    const heading = document.createElement('input');
    heading.type = 'text'; heading.maxLength = 200; heading.required = true; heading.value = idea.heading;
    headingLabel.append(heading);
    const explanationLabel = document.createElement('label');
    explanationLabel.textContent = 'What did you learn?';
    const explanation = document.createElement('textarea');
    explanation.rows = 5; explanation.maxLength = 20000; explanation.required = true; explanation.value = idea.explanation;
    explanationLabel.append(explanation);
    const remove = document.createElement('button');
    remove.type = 'button'; remove.textContent = 'Remove idea';
    remove.addEventListener('click', () => {
      if (cards.children.length === 1) return;
      card.remove(); update(); revision++; dirty = true; persist('draft');
    });
    card.append(legend, headingLabel, explanationLabel, remove);
    cards.append(card); update();
  }
  function update() {
    add.disabled = cards.children.length >= 10;
    [...cards.children].forEach(card => { card.querySelector('button').disabled = cards.children.length === 1; });
  }
  JSON.parse(document.getElementById('learning-initial').textContent).forEach(renderCard);
  add.addEventListener('click', () => {
    if (cards.children.length >= 10) return;
    renderCard({heading: '', explanation: ''}); revision++; dirty = true;
    persist('draft'); cards.lastElementChild.querySelector('input').focus();
  });
  form.addEventListener('input', () => {revision++; dirty = true; status.textContent = 'Unsaved changes';});
  form.addEventListener('focusout', event => {
    if (event.target.matches('input:not([type=hidden]), textarea') && !finalizing) persist('draft').catch(() => {});
  });
  form.addEventListener('submit', async event => {
    event.preventDefault(); finalizing = true; submit.disabled = true;
    try { await persist('save'); dirty = false; window.location.reload(); }
    catch (_) { finalizing = false; submit.disabled = false; }
  });
  window.addEventListener('beforeunload', event => {
    if (dirty) {event.preventDefault(); event.returnValue = '';}
  });
})();
