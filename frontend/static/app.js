const API = 'http://localhost:8000';
let ws = null;
let currentTaskId = null;
let currentTheme = 'dark';

// ---- TAB NAVIGATION ----
function showTab(name) {
  document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const panel = document.getElementById('tab-' + name);
  const btn = document.getElementById('nav-' + name);
  if (panel) panel.classList.add('active');
  if (btn) btn.classList.add('active');
  const breadcrumbs = { chat: 'agent-chat', pr: 'pr-review', repo: 'repo-analyzer', debug: 'debugger', agents: 'agent-registry' };
  document.getElementById('breadcrumb').innerHTML = `<span class="text-teal-400">~</span> / ${breadcrumbs[name] || name}`;
  if (name === 'agents') loadAgents();
}

// ---- HEALTH ----
async function checkHealth() {
  try {
    const r = await fetch(`${API}/health`);
    if (r.ok) setOnline(true);
    else setOnline(false);
  } catch { setOnline(false); }
}
function setOnline(online) {
  const dot = document.getElementById('statusDot');
  const txt = document.getElementById('statusText');
  const badge = document.getElementById('connBadge');
  dot.className = 'w-2 h-2 rounded-full status-dot ' + (online ? 'online' : 'offline');
  txt.textContent = online ? 'Connected' : 'Disconnected';
  badge.className = 'text-xs px-2 py-0.5 rounded-full font-mono ' + (online ? 'badge-online' : 'badge-offline');
  badge.textContent = online ? '● online' : '● offline';
}

// ---- TERMINAL LOG ----
function logLine(text, type = 'info') {
  const out = document.getElementById('terminalOutput');
  const line = document.createElement('div');
  line.className = `term-line ${type}`;
  line.textContent = text;
  out.appendChild(line);
  out.scrollTop = out.scrollHeight;
}
function clearLog() {
  document.getElementById('terminalOutput').innerHTML = '<div class="term-line dim">// Log cleared.</div>';
  document.getElementById('resultBlock').classList.add('hidden');
}

// ---- AGENT RUN ----
async function runAgent() {
  const task = document.getElementById('taskInput').value.trim();
  if (!task) return showToast('Please enter a task description', 'error');
  const agentType = document.getElementById('agentType').value;
  const btn = document.getElementById('runBtn');
  const icon = document.getElementById('runIcon');
  const label = document.getElementById('runLabel');

  btn.disabled = true;
  icon.className = 'fas fa-spinner fa-spin';
  label.textContent = 'Running…';
  document.getElementById('resultBlock').classList.add('hidden');

  const taskId = 'task_' + Date.now();
  currentTaskId = taskId;
  logLine(`[${new Date().toLocaleTimeString()}] Starting ${agentType} agent…`, 'info');
  logLine(`[${new Date().toLocaleTimeString()}] Task: ${task}`, 'dim');

  // Connect WebSocket first
  connectWS(taskId);

  try {
    const r = await fetch(`${API}/api/v1/agent/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ agent_type: agentType, task, task_id: taskId })
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    logLine(`[${new Date().toLocaleTimeString()}] Agent started. Task ID: ${data.task_id || taskId}`, 'success');
    if (data.result) showResult(data.result);
  } catch (e) {
    logLine(`[${new Date().toLocaleTimeString()}] Error: ${e.message}`, 'error');
    showToast(`Backend error: ${e.message}`, 'error');
    btn.disabled = false;
    icon.className = 'fas fa-play';
    label.textContent = 'Run Agent';
  }
}

function connectWS(taskId) {
  if (ws) ws.close();
  const wsUrl = `ws://localhost:8000/ws/agent/${taskId}`;
  logLine(`[WS] Connecting to ${wsUrl}…`, 'dim');
  try {
    ws = new WebSocket(wsUrl);
    ws.onopen = () => logLine('[WS] Stream connected.', 'success');
    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        if (msg.type === 'error') {
          logLine(`[ERROR] ${msg.message}`, 'error');
        } else if (msg.type === 'done') {
          logLine(`[DONE] ${msg.message || 'Agent completed.'}`, 'success');
          if (msg.result) showResult(msg.result);
          resetRunBtn();
        } else if (msg.type === 'chunk' || msg.message) {
          logLine(`[LOG] ${msg.message || msg.content || JSON.stringify(msg)}`, 'info');
        }
      } catch { logLine(`[RAW] ${e.data}`, 'dim'); }
    };
    ws.onerror = () => logLine('[WS] Connection error.', 'error');
    ws.onclose = () => { logLine('[WS] Stream closed.', 'dim'); resetRunBtn(); };
  } catch (e) { logLine(`[WS] Failed: ${e.message}`, 'error'); }
}

function resetRunBtn() {
  const btn = document.getElementById('runBtn');
  const icon = document.getElementById('runIcon');
  const label = document.getElementById('runLabel');
  btn.disabled = false;
  icon.className = 'fas fa-play';
  label.textContent = 'Run Agent';
}

function showResult(result) {
  const block = document.getElementById('resultBlock');
  const code = document.getElementById('resultCode');
  block.classList.remove('hidden');
  const txt = typeof result === 'string' ? result : JSON.stringify(result, null, 2);
  code.textContent = txt;
  hljs.highlightElement(code);
  logLine(`[RESULT] Code block updated.`, 'success');
}

function copyResult() {
  const txt = document.getElementById('resultCode').textContent;
  navigator.clipboard.writeText(txt).then(() => showToast('Copied to clipboard!', 'success'));
}

// ---- PR REVIEW ----
async function reviewPR() {
  const repoUrl = document.getElementById('prRepoUrl').value.trim();
  const prNumber = document.getElementById('prNumber').value;
  if (!repoUrl || !prNumber) return showToast('Please enter repo URL and PR number', 'error');

  const container = document.getElementById('prResults');
  container.innerHTML = '<div class="glass-card rounded-xl p-4 text-sm text-slate-400 font-mono animate-pulse">Reviewing PR…</div>';
  try {
    const r = await fetch(`${API}/api/v1/pr/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl, pr_number: parseInt(prNumber) })
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    renderFindings(container, data.findings || data.result || data, 'PR');
  } catch (e) {
    container.innerHTML = `<div class="finding-card critical"><span class="text-red-400 font-mono text-sm">Error: ${e.message}</span></div>`;
    showToast(`Review failed: ${e.message}`, 'error');
  }
}

// ---- REPO ANALYZE ----
async function analyzeRepo() {
  const repoUrl = document.getElementById('repoUrl').value.trim();
  if (!repoUrl) return showToast('Please enter a repository URL', 'error');

  const container = document.getElementById('repoResults');
  container.innerHTML = '<div class="glass-card rounded-xl p-4 text-sm text-slate-400 font-mono animate-pulse">Analyzing repository…</div>';
  try {
    const r = await fetch(`${API}/api/v1/repo/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl })
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    renderFindings(container, data.findings || data.result || [data], 'Repo');
  } catch (e) {
    container.innerHTML = `<div class="finding-card critical"><span class="text-red-400 font-mono text-sm">Error: ${e.message}</span></div>`;
    showToast(`Analysis failed: ${e.message}`, 'error');
  }
}

// ---- DEBUG ----
async function debugCode() {
  const code = document.getElementById('debugCode').value.trim();
  const error = document.getElementById('debugError').value.trim();
  if (!code) return showToast('Please paste the code to debug', 'error');

  const container = document.getElementById('debugResults');
  container.innerHTML = '<div class="glass-card rounded-xl p-4 text-sm text-slate-400 font-mono animate-pulse">Analyzing with AI…</div>';
  try {
    const r = await fetch(`${API}/api/v1/debug`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code, error })
    });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const data = await r.json();
    const suggestions = data.suggestions || data.result || [data];
    container.innerHTML = '';
    (Array.isArray(suggestions) ? suggestions : [suggestions]).forEach(s => {
      const card = document.createElement('div');
      card.className = 'finding-card info';
      card.innerHTML = `
        <div class="flex items-center gap-2 mb-2">
          <span class="text-teal-400 font-mono text-xs">SUGGESTION</span>
        </div>
        <div class="text-sm text-slate-300">${typeof s === 'string' ? s : s.message || JSON.stringify(s)}</div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    container.innerHTML = `<div class="finding-card critical"><span class="text-red-400 font-mono text-sm">Error: ${e.message}</span></div>`;
    showToast(`Debug failed: ${e.message}`, 'error');
  }
}

// ---- AGENTS LIST ----
async function loadAgents() {
  const container = document.getElementById('agentsList');
  try {
    const r = await fetch(`${API}/api/v1/agents`);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const agents = await r.json();
    container.innerHTML = '';
    (Array.isArray(agents) ? agents : [agents]).forEach(agent => {
      const card = document.createElement('div');
      card.className = 'agent-card';
      card.innerHTML = `
        <div class="flex items-center gap-3 mb-2">
          <div class="w-8 h-8 rounded-lg bg-gradient-to-br from-teal-500/20 to-purple-500/20 flex items-center justify-center text-teal-400">
            <i class="fas fa-robot text-sm"></i>
          </div>
          <div class="font-semibold text-sm text-white">${agent.name || agent.id || 'Agent'}</div>
        </div>
        <div class="text-xs text-slate-500">${agent.description || 'AI-powered agent'}</div>
        <div class="mt-2 flex gap-2 flex-wrap">
          ${(agent.capabilities || []).map(c => `<span class="text-xs px-2 py-0.5 rounded-full bg-white/5 text-slate-400">${c}</span>`).join('')}
        </div>
      `;
      container.appendChild(card);
    });
  } catch (e) {
    container.innerHTML = `
      <div class="agent-card"><div class="text-sm text-teal-400 font-mono">coding-agent</div><div class="text-xs text-slate-500 mt-1">Write, refactor, and generate code using AI</div></div>
      <div class="agent-card"><div class="text-sm text-purple-400 font-mono">review-agent</div><div class="text-xs text-slate-500 mt-1">Code review and quality analysis</div></div>
      <div class="agent-card"><div class="text-sm text-orange-400 font-mono">bugfix-agent</div><div class="text-xs text-slate-500 mt-1">Identify and fix bugs automatically</div></div>
    `;
  }
}

// ---- FINDINGS RENDERER ----
function renderFindings(container, data, prefix) {
  container.innerHTML = '';
  if (!data || (Array.isArray(data) && data.length === 0)) {
    container.innerHTML = '<div class="glass-card rounded-xl p-4 text-sm text-slate-400 font-mono">No findings returned.</div>';
    return;
  }
  const items = Array.isArray(data) ? data : [data];
  items.slice(0, 20).forEach(item => {
    const sev = (item.severity || 'info').toLowerCase();
    const card = document.createElement('div');
    card.className = `finding-card ${sev}`;
    card.innerHTML = `
      <div class="flex items-start justify-between gap-2 mb-2">
        <span class="font-semibold text-sm text-white">${item.title || item.message || prefix + ' Finding'}</span>
        <span class="text-xs px-2 py-0.5 rounded-full font-mono uppercase" style="background:rgba(255,255,255,0.05)">${sev}</span>
      </div>
      <div class="text-xs text-slate-400 leading-relaxed">${item.description || item.content || JSON.stringify(item)}</div>
      ${item.line ? `<div class="text-xs text-slate-600 font-mono mt-1">Line ${item.line}</div>` : ''}
    `;
    container.appendChild(card);
  });
  showToast(`${items.length} finding(s) returned`, 'success');
}

// ---- SIDEBAR TOGGLE ----
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('mobileOverlay');
  sidebar.classList.toggle('open');
  overlay.classList.toggle('hidden');
}

// ---- THEME TOGGLE ----
function toggleTheme() {
  currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.body.classList.toggle('light', currentTheme === 'light');
}

// ---- TOAST ----
function showToast(msg, type = 'info') {
  const container = document.getElementById('toastContainer');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fas fa-${type === 'error' ? 'circle-xmark' : type === 'success' ? 'circle-check' : 'circle-info'} mr-2"></i>${msg}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// ---- INIT ----
checkHealth();
setInterval(checkHealth, 15000);
