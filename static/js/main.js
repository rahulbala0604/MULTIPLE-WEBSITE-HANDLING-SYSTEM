/* ─────────────────────────────────────────────
   ADMATRIX PRO — CORE JS
   ───────────────────────────────────────────── */

// ── MODAL ──
function openModal(title, bodyHTML) {
  document.getElementById('modalTitle').textContent = title;
  document.getElementById('modalBody').innerHTML = bodyHTML;
  document.getElementById('modalOverlay').classList.add('open');
}
function closeModal() {
  document.getElementById('modalOverlay').classList.remove('open');
}

// ── TOAST ──
function toast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const el = document.createElement('div');
  el.className = `toast toast-${type}`;
  const icons = { success: '✓', error: '✕', info: '◈' };
  el.innerHTML = `<span>${icons[type] || '◈'}</span><span>${msg}</span>`;
  container.appendChild(el);
  setTimeout(() => el.remove(), 3500);
}

// ── SIDEBAR TOGGLE ──
function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('open');
}

// ── API HELPERS ──
async function apiGet(url) {
  const res = await fetch(url);
  return res.json();
}

async function apiPost(url, data) {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

async function apiPut(url, data) {
  const res = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  return res.json();
}

async function apiDelete(url) {
  const res = await fetch(url, { method: 'DELETE' });
  return res.json();
}

// ── TABLE SEARCH ──
function filterTable(inputId, tableId) {
  const query = document.getElementById(inputId).value.toLowerCase();
  const rows = document.querySelectorAll(`#${tableId} tbody tr`);
  rows.forEach(row => {
    row.style.display = row.textContent.toLowerCase().includes(query) ? '' : 'none';
  });
}

// ── BADGE HELPER ──
function statusBadge(status) {
  const map = {
    active: 'badge-active',
    inactive: 'badge-inactive',
    paused: 'badge-paused',
    high: 'badge-high',
    medium: 'badge-medium',
    low: 'badge-low',
  };
  return `<span class="badge ${map[status] || 'badge-medium'}">${status}</span>`;
}

// ── CURRENCY FORMAT ──
function fmtCurrency(v) {
  return '₹' + Number(v || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
}

function fmtNum(v) {
  return Number(v || 0).toLocaleString('en-IN');
}

function fmtPct(v) {
  return Number(v || 0).toFixed(2) + '%';
}

// ── LOAD TOP BAR STATS ──
async function loadTopBarStats() {
  try {
    const data = await apiGet('/api/dashboard');
    const el1 = document.getElementById('todayImpressions');
    const el2 = document.getElementById('topCtr');
    if (el1) el1.textContent = fmtNum(data.total_impressions);
    if (el2) el2.textContent = fmtPct(data.ctr);
  } catch(e) {}
}

// ── BAR CHART RENDERER ──
function renderBarChart(containerId, data, maxVal, colorClass = 'bar-imp') {
  const container = document.getElementById(containerId);
  if (!container) return;
  const max = maxVal || Math.max(...data.map(d => d.value), 1);
  container.innerHTML = data.map(d => `
    <div class="bar-col">
      <div class="bar ${colorClass}" style="height:${Math.max((d.value/max)*100,2)}%"
           title="${d.label}: ${fmtNum(d.value)}"></div>
      <span class="bar-label">${d.label}</span>
    </div>
  `).join('');
}

// ── PROGRESS LIST RENDERER ──
function renderProgressList(containerId, items, maxVal) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const max = maxVal || Math.max(...items.map(i => i.value), 1);
  container.innerHTML = items.map(item => `
    <div class="progress-item">
      <div class="progress-header">
        <span class="progress-name">${item.name}</span>
        <span class="progress-val">${fmtNum(item.value)}</span>
      </div>
      <div class="progress-bar-track">
        <div class="progress-bar-fill" style="width:${(item.value/max)*100}%"></div>
      </div>
    </div>
  `).join('');
}

// ── CONFIRM DELETE ──
function confirmDelete(msg, callback) {
  const html = `
    <div style="text-align:center;padding:12px 0">
      <div style="font-size:40px;margin-bottom:12px">⚠</div>
      <p style="color:var(--text-secondary);margin-bottom:20px">${msg}</p>
      <div class="btn-group" style="justify-content:center">
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn btn-danger" onclick="closeModal();(${callback})()">Delete</button>
      </div>
    </div>`;
  openModal('Confirm Action', html);
}

// Init on load
document.addEventListener('DOMContentLoaded', loadTopBarStats);
