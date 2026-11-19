(() => {
  const viewer = document.getElementById('learning-viewer');
  if (!viewer) return;
  const open = document.getElementById('open-learning-viewer');
  const close = document.getElementById('close-learning-viewer');
  const previous = document.getElementById('learning-previous');
  const next = document.getElementById('learning-next');
  const slide = document.getElementById('learning-slide');
  const status = document.getElementById('learning-slide-status');
  const days = [...document.querySelectorAll('.learning-day')];
  let index = 0;
  document.getElementById('learning-month').addEventListener('change', event => {
    if (event.target.value && event.target.validity.valid) document.getElementById('learning-month-form').requestSubmit();
  });
  function position() {
    const sidebar = document.querySelector('.portfolio-sidebar')?.getBoundingClientRect();
    const header = document.getElementById('header')?.getBoundingClientRect();
    const wide = window.matchMedia('(min-width: 801px)').matches;
    const left = wide && sidebar ? Math.max(0, sidebar.right) : 0;
    const top = Math.max(0, header?.bottom || 0);
    const width = window.innerWidth - left;
    const height = window.innerHeight - top;
    viewer.style.left = `${left + width * .025}px`;
    viewer.style.top = `${top + height * .04}px`;
    viewer.style.width = `${width * .95}px`;
    viewer.style.height = `${height * .92}px`;
  }
  function show() {
    slide.replaceChildren();
    if (!days.length) {
      const empty = document.createElement('p');
      empty.textContent = 'No saved learnings for this month yet. Add your first idea below the journal.';
      slide.append(empty);
      status.textContent = 'No saved days';
    } else {
      const day = days[index];
      const title = document.createElement('h3');
      title.className = 'learning-slide-date'; title.textContent = day.querySelector('h3').textContent;
      slide.append(title);
      day.querySelectorAll('details').forEach(idea => {
        const section = document.createElement('section'); section.className = 'learning-slide-idea';
        const heading = document.createElement('h4'); heading.textContent = idea.querySelector('summary').textContent;
        section.append(heading, idea.querySelector('.learning-explanation').cloneNode(true));
        slide.append(section);
      });
      status.textContent = `Day ${index + 1} of ${days.length}`;
    }
    previous.disabled = index === 0;
    next.disabled = index >= days.length - 1;
    slide.scrollTop = 0;
  }
  open.addEventListener('click', () => {index = 0; show(); position(); viewer.showModal(); close.focus();});
  close.addEventListener('click', () => viewer.close());
  viewer.addEventListener('close', () => open.focus());
  previous.addEventListener('click', () => {if (index > 0) {index--; show();}});
  next.addEventListener('click', () => {if (index < days.length - 1) {index++; show();}});
  viewer.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft' && index > 0) {event.preventDefault(); index--; show();}
    if (event.key === 'ArrowRight' && index < days.length - 1) {event.preventDefault(); index++; show();}
  });
  window.addEventListener('resize', () => {if (viewer.open) position();});
})();
