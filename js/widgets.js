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

  /* ================================================================
     PRODUCTIVITY WIDGETS
     Today's Tasks · Recent Activity · Quick Actions ·
     Upcoming Deadlines · Streak Leaderboard
     Reads via OFXAuth.sb (already-authenticated client + RLS).
     Renders into the same #panel-widgets mount, below the bar above —
     works on both the Team Portal and the Admin Panel.
  ================================================================ */
  function pCardHTML(id, title, badgeId) {
    return `<div class="pw-card" id="${id}" style="background:var(--panel-2);border:1px solid var(--line);border-radius:14px;padding:16px 20px;display:flex;flex-direction:column">
      <div style="font-size:.72rem;color:var(--muted);text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px;display:flex;align-items:center;gap:8px">
        <span>${title}</span>
        ${badgeId ? `<span id="${badgeId}" style="display:none;background:var(--accent);color:#0B0E14;border-radius:20px;padding:1px 8px;font-size:.68rem;font-weight:700"></span>` : ''}
      </div>
      <div id="${id}-body" style="font-size:.86rem;color:var(--text);flex:1">Loading…</div>
    </div>`;
  }

  function productivityGridHTML() {
    return `<div class="pw-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px;margin-bottom:24px">
      ${pCardHTML('pw-quick', '⚡ Quick Actions')}
      ${pCardHTML('pw-today', "📋 Today's Tasks", 'pw-today-badge')}
      ${pCardHTML('pw-deadlines', '⏰ Upcoming Deadlines')}
      ${pCardHTML('pw-activity', '🕒 Recent Activity')}
      ${pCardHTML('pw-leaderboard', '🔥 Streak Leaderboard')}
    </div>`;
  }

  function relativeTime(iso) {
    if (!iso) return '—';
    const diffSec = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
    if (diffSec < 60)    return 'Just now';
    if (diffSec < 3600)  return `${Math.floor(diffSec/60)}m ago`;
    if (diffSec < 86400) return `${Math.floor(diffSec/3600)}h ago`;
    return `${Math.floor(diffSec/86400)}d ago`;
  }

  const rowStyle = 'display:flex;align-items:center;gap:8px;padding:7px 0;border-bottom:1px solid var(--line-soft)';

  /* ---------- 1. Quick Actions ---------- */
  // Each entry maps to a button that already exists somewhere on THIS page
  // (Team Portal or Admin Panel) — we just surface the most useful ones in
  // one place and "click" the real button so all existing logic still runs.
  // `section` (optional) is a sidebar/tab data-section to switch to first.
  const QUICK_ACTIONS = [
    { id: 'add-task-btn',        label: 'New Task',        icon: '✅' },
    { id: 'add-project-btn',     label: 'New Project',     icon: '📁' },
    { id: 'admin-add-proj-btn',  label: 'New Project',     icon: '📁' },
    { id: 'manual-log-btn',      label: 'Log Time',        icon: '⏱️', section: 'timetracker' },
    { id: 'ss-upload-btn',       label: 'Upload Screenshot', icon: '📤', section: 'screenshots' },
    { id: 'add-client-btn',      label: 'Add Client',      icon: '🧑‍💼' },
    { id: 'add-product-btn',     label: 'New Product',     icon: '🛍️' },
    { id: 'add-course-btn',      label: 'New Course',      icon: '🎓' },
    { id: 'add-coupon-btn',      label: 'New Coupon',      icon: '🏷️' },
  ];
  function loadQuickActions() {
    const body = document.getElementById('pw-quick-body');
    if (!body) return;
    const found = QUICK_ACTIONS.filter(a => document.getElementById(a.id));
    if (!found.length) { body.innerHTML = '<div style="color:var(--muted)">No quick actions available here.</div>'; return; }
    body.innerHTML = `<div style="display:flex;flex-wrap:wrap;gap:8px">${found.map(a =>
      `<button type="button" class="btn btn-ghost btn-sm pw-qa-btn" data-target="${a.id}" data-section="${a.section||''}">${a.icon} ${a.label}</button>`
    ).join('')}</div>`;
    body.querySelectorAll('.pw-qa-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const sectionName = btn.dataset.section;
        if (sectionName) {
          const navBtn = document.querySelector(`.sidebar-link[data-section="${sectionName}"]`);
          if (navBtn) navBtn.click();
        }
        const target = document.getElementById(btn.dataset.target);
        if (target) setTimeout(() => target.click(), sectionName ? 80 : 0);
      });
    });
  }

  /* ---------- 2. Today's Tasks ---------- */
  async function loadTodayTasks() {
    const body  = document.getElementById('pw-today-body');
    const badge = document.getElementById('pw-today-badge');
    if (!body) return;
    const sb = window.OFXAuth?.sb;
    if (!sb) { body.textContent = 'Unavailable.'; return; }
    try {
      const session = await OFXAuth.getSession();
      if (!session) { body.innerHTML = '<div style="color:var(--muted)">Sign in to see your tasks.</div>'; return; }
      const today = new Date().toISOString().split('T')[0];
      const { data } = await sb.from('tasks')
        .select('id,title,priority,status,due_date,project:projects(title)')
        .eq('assigned_to', session.user.id)
        .eq('due_date', today)
        .neq('status', 'done')
        .order('priority', { ascending: false });
      const tasks = data || [];
      if (badge) { badge.textContent = tasks.length; badge.style.display = tasks.length ? '' : 'none'; }
      if (!tasks.length) { body.innerHTML = '<div style="color:var(--muted)">🎉 Nothing due today — you\'re all caught up!</div>'; return; }
      const pColor = { low:'#5E6776', medium:'#FFC23D', high:'#FF8A3D', urgent:'#FF3B57' };
      body.innerHTML = tasks.map(t => `
        <div style="${rowStyle}">
          <span style="width:7px;height:7px;border-radius:50%;background:${pColor[t.priority]||pColor.medium};flex:none"></span>
          <div style="min-width:0;flex:1">
            <div style="color:var(--white);font-size:.84rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${t.title}</div>
            ${t.project?.title ? `<div style="font-size:.72rem;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${t.project.title}</div>` : ''}
          </div>
        </div>`).join('');
    } catch (e) { body.innerHTML = '<div style="color:var(--muted)">Could not load today\'s tasks.</div>'; }
  }

  /* ---------- 3. Upcoming Deadlines ---------- */
  async function loadDeadlines() {
    const body = document.getElementById('pw-deadlines-body');
    if (!body) return;
    const sb = window.OFXAuth?.sb;
    if (!sb) { body.textContent = 'Unavailable.'; return; }
    try {
      const today = new Date(); today.setHours(0,0,0,0);
      const horizon = new Date(today); horizon.setDate(horizon.getDate() + 7);
      const todayStr   = today.toISOString().split('T')[0];
      const horizonStr = horizon.toISOString().split('T')[0];
      const [{ data: tasks }, { data: projects }] = await Promise.all([
        sb.from('tasks').select('id,title,due_date').neq('status','done').gte('due_date', todayStr).lte('due_date', horizonStr),
        sb.from('projects').select('id,title,deadline').neq('status','completed').gte('deadline', todayStr).lte('deadline', horizonStr),
      ]);
      const items = [
        ...(tasks||[]).map(t => ({ type: 'Task',    title: t.title, date: t.due_date })),
        ...(projects||[]).map(p => ({ type: 'Project', title: p.title, date: p.deadline })),
      ].filter(it => it.date).sort((a,b) => new Date(a.date) - new Date(b.date)).slice(0, 6);
      if (!items.length) { body.innerHTML = '<div style="color:var(--muted)">No deadlines in the next 7 days. 🎈</div>'; return; }
      body.innerHTML = items.map(it => {
        const days = Math.round((new Date(it.date) - today) / 86400000);
        const dueLabel = days <= 0 ? 'Today' : days === 1 ? 'Tomorrow' : `In ${days} days`;
        const urgent = days <= 1;
        return `<div style="${rowStyle};justify-content:space-between">
          <div style="min-width:0">
            <div style="color:var(--white);font-size:.84rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${it.title}</div>
            <div style="font-size:.72rem;color:var(--muted)">${it.type}</div>
          </div>
          <span style="font-size:.74rem;font-weight:700;color:${urgent?'#FF3B57':'var(--accent)'};white-space:nowrap;margin-left:10px">${dueLabel}</span>
        </div>`;
      }).join('');
    } catch (e) { body.innerHTML = '<div style="color:var(--muted)">Could not load deadlines.</div>'; }
  }

  /* ---------- 4. Recent Activity ---------- */
  async function loadRecentActivity() {
    const body = document.getElementById('pw-activity-body');
    if (!body) return;
    const sb = window.OFXAuth?.sb;
    if (!sb) { body.textContent = 'Unavailable.'; return; }
    try {
      const [{ data: tasks }, { data: projects }] = await Promise.all([
        sb.from('tasks').select('id,title,status,updated_at').order('updated_at',{ascending:false}).limit(5),
        sb.from('projects').select('id,title,status,updated_at').order('updated_at',{ascending:false}).limit(5),
      ]);
      const items = [
        ...(tasks||[]).map(t => ({ icon: t.status==='done' ? '✅' : '📝', text: `Task “${t.title}” — ${String(t.status||'').replace('_',' ')}`, at: t.updated_at })),
        ...(projects||[]).map(p => ({ icon: '📁', text: `Project “${p.title}” — ${String(p.status||'').replace('_',' ')}`, at: p.updated_at })),
      ].filter(it => it.at).sort((a,b) => new Date(b.at) - new Date(a.at)).slice(0, 6);
      if (!items.length) { body.innerHTML = '<div style="color:var(--muted)">No recent activity yet.</div>'; return; }
      body.innerHTML = items.map(it => `
        <div style="${rowStyle};align-items:flex-start">
          <span style="flex:none">${it.icon}</span>
          <div style="min-width:0">
            <div style="color:var(--text);font-size:.8rem;line-height:1.4;overflow:hidden;text-overflow:ellipsis;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical">${it.text}</div>
            <div style="font-size:.7rem;color:var(--muted);margin-top:1px">${relativeTime(it.at)}</div>
          </div>
        </div>`).join('');
    } catch (e) { body.innerHTML = '<div style="color:var(--muted)">Could not load activity.</div>'; }
  }

  /* ---------- 5. Streak Leaderboard ---------- */
  async function loadLeaderboard() {
    const body = document.getElementById('pw-leaderboard-body');
    if (!body) return;
    const sb = window.OFXAuth?.sb;
    if (!sb) { body.textContent = 'Unavailable.'; return; }
    try {
      const { data } = await sb.from('profiles')
        .select('id,full_name,email,login_streak')
        .in('role', ['team','admin','super_admin'])
        .order('login_streak', { ascending: false })
        .limit(5);
      const rows = (data||[]).filter(p => (p.login_streak||0) > 0);
      if (!rows.length) { body.innerHTML = '<div style="color:var(--muted)">No active streaks yet — log in daily to start one! 🔥</div>'; return; }
      const medals = ['🥇','🥈','🥉'];
      body.innerHTML = rows.map((p,i) => `
        <div style="${rowStyle};justify-content:space-between">
          <div style="display:flex;align-items:center;gap:8px;min-width:0">
            <span style="width:20px;text-align:center;flex:none">${medals[i] || `#${i+1}`}</span>
            <span style="color:var(--white);font-size:.84rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">${p.full_name || p.email || 'Unknown'}</span>
          </div>
          <span style="font-size:.8rem;font-weight:700;color:#FFC23D;white-space:nowrap;margin-left:10px">🔥 ${p.login_streak} day${p.login_streak===1?'':'s'}</span>
        </div>`).join('');
    } catch (e) { body.innerHTML = '<div style="color:var(--muted)">Could not load leaderboard. (Needs the "Team can view team profiles" RLS policy.)</div>'; }
  }

  function init() {
    const mount = document.getElementById('panel-widgets');
    if (!mount) return;
    mount.innerHTML = widgetHTML() + productivityGridHTML();
    startClock();
    startWeather();
    startFocusMode();
    loadQuickActions();
    loadTodayTasks();
    loadDeadlines();
    loadRecentActivity();
    loadLeaderboard();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
