const API = () => "https://shatakshi-nestack-submission.onrender.com";
let currentFilter = 'all';
let allEvents = [];
let autoRefreshTimer = null;



function showView(v) {
  document.getElementById('view-dashboard').style.display = v === 'dashboard' ? '' : 'none';
  document.getElementById('view-create').style.display   = v === 'create'    ? '' : 'none';
  document.getElementById('viewTitle').textContent = v === 'dashboard' ? 'Dashboard' : 'Create Event';
  document.querySelectorAll('.nav .nav-item').forEach(el => el.classList.remove('active'));
  if (v === 'dashboard') document.querySelectorAll('.nav-item')[0].classList.add('active');
  if (v === 'create')    document.querySelectorAll('.nav-item')[1].classList.add('active');
}

function filterNav(s) {
  setFilter(s);
  showView('dashboard');
}


function setFilter(status) {
  currentFilter = status;
  document.querySelectorAll('.filter-btn').forEach(b => {
    b.classList.toggle('active', b.dataset.status === status);
  });
  renderTable(allEvents);
}


async function refreshAll() {
  const icon = document.getElementById('refreshIcon');
  icon.classList.add('refreshing');
  await Promise.all([fetchEvents(), checkHealth()]);
  icon.classList.remove('refreshing');
  document.getElementById('lastRefresh').textContent =
    'Refreshed ' + new Date().toLocaleTimeString();
}

async function fetchEvents() {
  try {
    const res = await fetch(`${API()}/events`);
    if (!res.ok) throw new Error(res.status);
    const text = await res.text();
console.log(text);

let data = {};
try {
  data = JSON.parse(text);
} catch {
  data = { error: text };
}
    allEvents = data.events || [];
    renderStats(allEvents);
    renderTable(allEvents);
  } catch(e) {
    renderTableError();
  }
}

function renderStats(events) {
  const count = s => events.filter(e => e.status === s).length;
  document.getElementById('stat-total').textContent     = events.length;
  document.getElementById('stat-delivered').textContent = count('delivered');
  document.getElementById('stat-pending').textContent   = count('pending') + count('processing');
  document.getElementById('stat-dead').textContent      = count('dead');
}

function renderTable(events) {
  const filtered = currentFilter === 'all'
    ? events
    : events.filter(e => e.status === currentFilter);

  const tbody = document.getElementById('eventTableBody');
  if (!filtered.length) {
    tbody.innerHTML = `<tr><td colspan="6">
      <div class="empty">
        <div class="empty-icon">◎</div>
        <div class="empty-text">No events${currentFilter !== 'all' ? ' with status <strong>'+currentFilter+'</strong>' : ''}.<br/>Fire a webhook to get started.</div>
      </div></td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(e => `
    <tr onclick="openDrawer('${e.id}')">
      <td><span class="event-id">${e.id.slice(0,8)}…</span></td>
      <td><span class="event-type">${escHtml(e.type)}</span></td>
      <td><span class="event-url" title="${escHtml(e.webhook_url)}">${escHtml(e.webhook_url)}</span></td>
      <td><span class="badge ${e.status}">${e.status}</span></td>
      <td><span class="retry-pill">${e.retry_count}/3</span></td>
      <td style="color:var(--muted);font-size:11px;">${fmtDate(e.created_at)}</td>
    </tr>`).join('');
}

function renderTableError() {
  document.getElementById('eventTableBody').innerHTML = `<tr><td colspan="6">
    <div class="empty">
      <div class="empty-icon">⚠</div>
      <div class="empty-text">Cannot reach API at <strong>${API()}</strong><br/>Make sure <code>python run.py</code> is running.</div>
    </div></td></tr>`;
}


async function checkHealth() {
  try {
    const res = await fetch(`${API()}/health`);
    const ok  = res.ok;
    document.getElementById('serverPulse').className = ok ? 'pulse' : 'pulse dead';
    document.getElementById('serverStatusText').textContent = ok ? 'online' : 'offline';
    document.getElementById('serverStatusText').style.color = ok ? 'var(--green)' : 'var(--red)';
  } catch {
    document.getElementById('serverPulse').className = 'pulse dead';
    document.getElementById('serverStatusText').textContent = 'offline';
    document.getElementById('serverStatusText').style.color = 'var(--red)';
  }
}


async function createWebhookEvent() {
  const type = document.getElementById('c-type').value.trim();
  const url  = document.getElementById('c-url').value.trim();
  const raw  = document.getElementById('c-payload').value.trim();

  if (!type) { toast('Event type is required', 'error'); return; }
  if (!url)  { toast('Webhook URL is required', 'error'); return; }
  let payload;
  try { payload = JSON.parse(raw); }
  catch { toast('Payload must be valid JSON', 'error'); return; }

  try {
    const res = await fetch(`${API()}/events`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({type, payload, webhook_url: url})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || res.status);
    toast('Event created & queued ✓', 'success');
    document.getElementById('c-type').value = '';
    document.getElementById('c-url').value  = '';
    document.getElementById('c-payload').value = '{\n  \n}';
    showView('dashboard');
    await refreshAll();
  } catch(e) {
    toast('Error: ' + e.message, 'error');
  }
}


async function quickFire() {
  const type = document.getElementById('q-type').value.trim();
  const url  = document.getElementById('q-url').value.trim();
  const raw  = document.getElementById('q-payload').value.trim();
  if (!type || !url) { toast('Fill in type and URL', 'error'); return; }
  let payload;
  try { payload = JSON.parse(raw); }
  catch { toast('Payload must be valid JSON', 'error'); return; }

  try {
    const res = await fetch(`${API()}/events`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({type, payload, webhook_url: url})
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error || res.status);
    toast(`⚡ Fired: ${type}`, 'success');
    await refreshAll();
  } catch(e) {
    toast('Error: ' + e.message, 'error');
  }
}


async function openDrawer(id) {
  document.getElementById('drawerOverlay').classList.add('open');
  document.getElementById('drawer').classList.add('open');
  document.getElementById('drawerBody').innerHTML = `<div style="text-align:center;padding:40px;"><div class="spinner"></div></div>`;
  document.getElementById('drawerFooter').innerHTML = '';

  try {
    const res  = await fetch(`${API()}/events/${id}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    renderDrawer(data);
  } catch(e) {
    document.getElementById('drawerBody').innerHTML = `<div class="empty"><div class="empty-icon">⚠</div><div class="empty-text">${e.message}</div></div>`;
  }
}

function renderDrawer(ev) {
  document.getElementById('drawerTitle').textContent = ev.type;
  document.getElementById('drawerSubtitle').innerHTML =
    `<span class="badge ${ev.status}" style="font-size:9px;">${ev.status}</span>
     &nbsp; <span style="color:var(--muted);">${ev.id}</span>`;

  const payload = (() => {
    try { return JSON.stringify(JSON.parse(ev.payload), null, 2); }
    catch { return ev.payload; }
  })();

  const attempts = (ev.attempts || []);

  document.getElementById('drawerBody').innerHTML = `
    <div class="detail-section">
      <div class="detail-section-title">Event Info</div>
      <div class="detail-row"><span class="detail-key">ID</span><span class="detail-val mono" style="font-size:11px;">${ev.id}</span></div>
      <div class="detail-row"><span class="detail-key">Type</span><span class="detail-val"><span class="event-type">${escHtml(ev.type)}</span></span></div>
      <div class="detail-row"><span class="detail-key">Status</span><span class="detail-val"><span class="badge ${ev.status}">${ev.status}</span></span></div>
      <div class="detail-row"><span class="detail-key">Retries</span><span class="detail-val">${ev.retry_count} / 3</span></div>
      <div class="detail-row"><span class="detail-key">Created</span><span class="detail-val">${fmtDateFull(ev.created_at)}</span></div>
      <div class="detail-row"><span class="detail-key">Next Retry</span><span class="detail-val">${ev.next_retry_at ? fmtDateFull(ev.next_retry_at) : '—'}</span></div>
      <div class="detail-row"><span class="detail-key">Target URL</span><span class="detail-val mono" style="font-size:11px;color:var(--cyan);">${escHtml(ev.webhook_url)}</span></div>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">Payload</div>
      <div class="code-block">${escHtml(payload)}</div>
    </div>

    <div class="detail-section">
      <div class="detail-section-title">Delivery Attempts (${attempts.length})</div>
      ${attempts.length === 0
        ? `<div style="color:var(--muted);font-size:11px;">No attempts yet — worker will pick this up shortly.</div>`
        : attempts.map((a, i) => `
          <div class="attempt ${a.outcome === 'success' ? 'success' : 'fail'}" data-num="${i+1}">
            <div class="attempt-top">
              <span class="badge ${a.outcome === 'success' ? 'delivered' : 'failed'}">${a.outcome}</span>
              ${a.http_status ? `<span class="retry-pill">HTTP ${a.http_status}</span>` : '<span class="retry-pill">no response</span>'}
            </div>
            <div class="attempt-time">${fmtDateFull(a.attempted_at)}</div>
            ${a.delivery_time_ms ? `<div class="attempt-detail">⏱ ${a.delivery_time_ms}ms</div>` : ''}
            ${a.error_message ? `<div class="attempt-detail" style="color:var(--red);">✕ ${escHtml(a.error_message)}</div>` : ''}
          </div>`).join('')
      }
    </div>`;


  let footerHtml = `<button class="btn btn-ghost" onclick="closeDrawer()">Close</button>`;
  if (ev.status === 'dead') {
    footerHtml = `
      <button class="btn btn-success" onclick="retryEvent('${ev.id}')">↩ Retry Dead Event</button>
      <button class="btn btn-ghost" onclick="closeDrawer()">Close</button>`;
  }
  document.getElementById('drawerFooter').innerHTML = footerHtml;
}

function closeDrawer() {
  document.getElementById('drawer').classList.remove('open');
  document.getElementById('drawerOverlay').classList.remove('open');
}

async function retryEvent(id) {
  try {
    const res  = await fetch(`${API()}/events/${id}/retry`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) throw new Error(data.error);
    toast('Event re-queued ✓', 'success');
    closeDrawer();
    await refreshAll();
  } catch(e) {
    toast('Retry failed: ' + e.message, 'error');
  }
}


function toast(msg, type = 'info') {
  const icons = { success: '✓', error: '✕', info: 'ℹ' };
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span>${icons[type]}</span><span>${msg}</span>`;
  document.getElementById('toastContainer').appendChild(el);
  setTimeout(() => el.remove(), 3500);
}


function escHtml(s) {
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
function fmtDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso + (iso.endsWith('Z') ? '' : 'Z'));
  return d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'}) + ' ' +
         d.toLocaleDateString([], {month:'short', day:'numeric'});
}
function fmtDateFull(iso) {
  if (!iso) return '—';
  const d = new Date(iso + (iso.endsWith('Z') ? '' : 'Z'));
  return d.toLocaleString();
}

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') closeDrawer();
  if (e.key === 'r' && !e.ctrlKey && !e.metaKey && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
    refreshAll();
  }
});


(async () => {
  await refreshAll();
 
  autoRefreshTimer = setInterval(refreshAll, 5000);
})();

