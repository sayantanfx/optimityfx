/* ============================================================
   OptimityFX — Panel dashboard widgets (clock / weather / focus)
   Renders into any element with id="panel-widgets".
   Weather: Open-Meteo (free, no API key) — falls back to Kolkata
   if geolocation is denied or unavailable.
   ============================================================ */
(function () {
  'use strict';

  const FALLBACK = { name: 'Kolkata', lat: 22.5726, lon: 88.3639 };

  // WMO weather codes -> { label, icon, bad }
  const WCODES = {
    0:['Clear sky','☀️',false], 1:['Mainly clear','🌤️',false], 2:['Partly cloudy','⛅',false], 3:['Overcast','☁️',false],
    45:['Fog','🌫️',true], 48:['Fog','🌫️',true],
    51:['Light drizzle','🌦️',true], 53:['Drizzle','🌦️',true], 55:['Heavy drizzle','🌧️',true],
    61:['Light rain','🌧️',true], 63:['Rain','🌧️',true], 65:['Heavy rain','🌧️',true],
    66:['Freezing rain','🌧️',true], 67:['Freezing rain','🌧️',true],
    71:['Light snow','🌨️',true], 73:['Snow','🌨️',true], 75:['Heavy snow','🌨️',true],
    80:['Rain showers','🌦️',true], 81:['Rain showers','🌧️',true], 82:['Violent showers','⛈️',true],
    95:['Thunderstorm','⛈️',true], 96:['Thunderstorm w/ hail','⛈️',true], 99:['Severe thunderstorm','⛈️',true],
  };

  function widgetHTML() {
    return `
    <div class="pw-bar" style="display:flex;flex-wrap:wrap;gap:14px;margin-bottom:20px">
      <div class="pw-card" id="pw-clock" style="flex:1;min-width:180px;background:var(--panel-2);border:1px solid var(--line);border-radius:14px;padding:16px 20px">
        <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px">Local Time</div>
        <div id="pw-clock-time" style="font-size:1.5rem;font-weight:700;color:var(--white);font-family:monospace">--:--:--</div>
        <div id="pw-clock-date" style="font-size:.78rem;color:var(--muted);margin-top:2px">—</div>
      </div>
      <div class="pw-card" id="pw-weather" style="flex:1;min-width:220px;background:var(--panel-2);border:1px solid var(--line);border-radius:14px;padding:16px 20px">
        <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px">Weather — <span id="pw-weather-loc">…</span></div>
        <div id="pw-weather-body" style="font-size:.92rem;color:var(--text)">Loading weather…</div>
      </div>
      <div class="pw-card" id="pw-focus" style="flex:1;min-width:180px;background:var(--panel-2);border:1px solid var(--line);border-radius:14px;padding:16px 20px;display:flex;flex-direction:column;justify-content:space-between">
        <div>
          <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px">Focus Mode</div>
          <div id="pw-focus-status" style="font-size:.92rem;color:var(--text)">Off — distractions visible</div>
        </div>
        <button class="btn btn-ghost btn-sm" id="pw-focus-btn" style="margin-top:10px;align-self:flex-start">Turn on Focus Mode</button>
      </div>
    </div>`;
  }

  function startClock() {
    const timeEl = document.getElementById('pw-clock-time');
    const dateEl = document.getElementById('pw-clock-date');
    if (!timeEl) return;
    const tick = () => {
      const now = new Date();
      timeEl.textContent = now.toLocaleTimeString('en-IN', { hour:'2-digit', minute:'2-digit', second:'2-digit' });
      dateEl.textContent = now.toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long' });
    };
    tick();
    setInterval(tick, 1000);
  }

  async function loadWeather(lat, lon, locName) {
    const locEl  = document.getElementById('pw-weather-loc');
    const bodyEl = document.getElementById('pw-weather-body');
    if (locEl) locEl.textContent = locName;
    try {
      const url = `https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weather_code&daily=weather_code,temperature_2m_max,precipitation_probability_max&timezone=auto&forecast_days=1`;
      const res = await fetch(url);
      const data = await res.json();
      const code = data?.current?.weather_code;
      const temp = Math.round(data?.current?.temperature_2m);
      const [label, icon, bad] = WCODES[code] || ['—','🌡️',false];
      const rainChance = data?.daily?.precipitation_probability_max?.[0];
      let html = `<div style="font-size:1.3rem;font-weight:700;color:var(--white)">${icon} ${isNaN(temp)?'—':temp+'°C'}</div>
                  <div style="margin-top:2px">${label}${rainChance!=null?` · ${rainChance}% rain chance today`:''}</div>`;
      if (bad || (rainChance != null && rainChance >= 60)) {
        html += `<div style="margin-top:10px;padding:8px 12px;background:rgba(255,194,61,.1);border:1px solid rgba(255,194,61,.3);border-radius:8px;font-size:.8rem;color:#FFC23D">⚠ Bad weather ahead — plan around possible delays today.</div>`;
      } else {
        html += `<div style="margin-top:10px;padding:8px 12px;background:rgba(34,224,122,.1);border:1px solid rgba(34,224,122,.3);border-radius:8px;font-size:.8rem;color:#22e07a">✓ Good conditions — clear skies for focused work.</div>`;
      }
      if (bodyEl) bodyEl.innerHTML = html;
    } catch (e) {
      if (bodyEl) bodyEl.textContent = 'Weather unavailable right now.';
    }
  }

  function startWeather() {
    if (!document.getElementById('pw-weather')) return;
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => loadWeather(pos.coords.latitude, pos.coords.longitude, 'Your location'),
        () => loadWeather(FALLBACK.lat, FALLBACK.lon, FALLBACK.name),
        { timeout: 5000 }
      );
    } else {
      loadWeather(FALLBACK.lat, FALLBACK.lon, FALLBACK.name);
    }
  }

  function startFocusMode() {
    const btn = document.getElementById('pw-focus-btn');
    const status = document.getElementById('pw-focus-status');
    if (!btn) return;
    const KEY = 'ofx_focus_mode';
    const apply = (on) => {
      document.body.classList.toggle('focus-mode', on);
      btn.textContent = on ? 'Turn off Focus Mode' : 'Turn on Focus Mode';
      status.textContent = on ? 'On — sidebar dimmed, stay in flow' : 'Off — distractions visible';
      localStorage.setItem(KEY, on ? '1' : '0');
    };
    btn.addEventListener('click', () => apply(!document.body.classList.contains('focus-mode')));
    apply(localStorage.getItem(KEY) === '1');
  }

  function init() {
    const mount = document.getElementById('panel-widgets');
    if (!mount) return;
    mount.innerHTML = widgetHTML();
    startClock();
    startWeather();
    startFocusMode();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
