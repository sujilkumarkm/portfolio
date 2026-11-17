(() => {
  const times = [...document.querySelectorAll('.interview-relative')];
  const dateParts = value => new Intl.DateTimeFormat('en-CA', {timeZone:'Europe/Dublin', year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(value);
  const dayNumber = value => {const parts=Object.fromEntries(dateParts(value).map(p=>[p.type,p.value])); return Date.UTC(+parts.year,+parts.month-1,+parts.day)/86400000;};
  function update() {
    const now = new Date();
    for (const time of times) {
      const date = new Date(time.dateTime), minutes = Math.ceil((date-now)/60000);
      if (!Number.isFinite(minutes)) continue;
      const days = dayNumber(date)-dayNumber(now);
      let label;
      if (minutes < -60) label = 'Scheduled time has passed';
      else if (minutes <= 0) label = 'Starting now / in progress';
      else if (minutes === 1) label = 'In less than a minute';
      else if (minutes < 60) label = `In ${minutes} minutes`;
      else if (days === 1) label = 'Tomorrow';
      else if (days > 1) label = `In ${days} days`;
      else { const hours=Math.floor(minutes/60), remainder=minutes%60; label=`Today · in ${hours} ${hours===1?'hour':'hours'}${remainder?` ${remainder} min`:''}`; }
      time.textContent = label;
    }
  }
  update();
  if (times.length) setInterval(update, 30000);
})();
