// === Métré BA Agent — Professional HMI Logic ===

const API = 'http://127.0.0.1:8765';
let selectedPlan = null;
let selectedRef = null;
let currentJobId = null;
let pollInterval = null;

// === Navigation ===
document.querySelectorAll('.nav-menu li').forEach(li => {
  li.addEventListener('click', () => {
    document.querySelectorAll('.nav-menu li').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    li.classList.add('active');
    document.getElementById(`page-${li.dataset.page}`).classList.add('active');
    if (li.dataset.page === 'repos') renderRepos();
    if (li.dataset.page === 'dashboard') renderDashboard();
  });
});

// === Backend Status ===
async function checkBackend() {
  try {
    const r = await fetch(`${API}/health`);
    const dot = document.querySelector('.status-dot');
    const txt = document.querySelector('.status-indicator span');
    if (r.ok) {
      dot.className = 'status-dot online';
      txt.textContent = 'Backend: connecté';
    }
  } catch {
    setTimeout(checkBackend, 2000);
  }
}
checkBackend();

// === Dashboard ===
function renderDashboard() {
  const modules = [
    { icon: 'fa-building', color: 'var(--accent-blue)', title: 'Ferraillage BAEL 91', desc: 'Calcul armatures poteaux, poutres, semelles selon BAEL 91', status: 'active' },
    { icon: 'fa-ruler-combined', color: 'var(--accent-green)', title: 'Eurocode 2', desc: 'Calcul sections acier, enrobage, classe structurale', status: 'active' },
    { icon: 'fa-eye', color: 'var(--accent-purple)', title: 'Vision IA Claude', desc: 'Extraction automatique poteaux, CH/LG, poutres', status: 'config' },
    { icon: 'fa-brain', color: 'var(--accent-cyan)', title: 'GLM-OCR', desc: 'OCR local open-source pour plans scannés', status: 'config' },
    { icon: 'fa-file-excel', color: 'var(--accent-green)', title: 'Métré Excel', desc: '3 feuilles: fondation, armatures, comparaison', status: 'active' },
    { icon: 'fa-file-pdf', color: 'var(--accent-red)', title: 'Rapport PDF', desc: 'Synthèse, insights, écarts documentés', status: 'active' },
    { icon: 'fa-file-alt', color: 'var(--accent-orange)', title: 'Rapport LaTeX', desc: 'Calculs BAEL/EC2 détaillés avec formules', status: 'config' },
    { icon: 'fa-chart-line', color: 'var(--accent-cyan)', title: 'Optimisation', desc: 'Barres 12m, chutes, regroupements', status: 'active' },
  ];
  const grid = document.getElementById('modulesGrid');
  grid.innerHTML = modules.map(m => `
    <div class="module-card">
      <div class="module-icon" style="background:${m.color}"><i class="fas ${m.icon}"></i></div>
      <h4>${m.title}</h4>
      <p>${m.desc}</p>
      <span class="module-status ${m.status}">${m.status === 'active' ? 'Actif' : 'Config'}</span>
    </div>
  `).join('');
}

// === File Upload ===
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone?.addEventListener('click', () => fileInput.click());
dropZone?.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone?.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone?.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length) handlePlanFile(e.dataTransfer.files[0]);
});
fileInput?.addEventListener('change', () => { if (fileInput.files.length) handlePlanFile(fileInput.files[0]); });

function handlePlanFile(file) {
  selectedPlan = file;
  document.getElementById('filesPreview').style.display = 'flex';
  document.getElementById('planCard').style.display = 'flex';
  document.getElementById('planFileName').textContent = file.name;
  document.getElementById('planFileSize').textContent = formatSize(file.size);
  document.getElementById('btnRun').disabled = false;
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / 1024 / 1024).toFixed(1) + ' MB';
}

document.getElementById('removePlan')?.addEventListener('click', () => {
  selectedPlan = null;
  document.getElementById('planCard').style.display = 'none';
  if (!selectedRef) document.getElementById('filesPreview').style.display = 'none';
  document.getElementById('btnRun').disabled = true;
});

document.getElementById('btnSelectRef')?.addEventListener('click', async () => {
  // Simulated file selection for reference
  selectedRef = { name: 'reference.xlsx', size: 65407 };
  document.getElementById('filesPreview').style.display = 'flex';
  document.getElementById('refCard').style.display = 'flex';
  document.getElementById('refFileName').textContent = 'metre_MZINDA.xlsx';
});

document.getElementById('removeRef')?.addEventListener('click', () => {
  selectedRef = null;
  document.getElementById('refCard').style.display = 'none';
  if (!selectedPlan) document.getElementById('filesPreview').style.display = 'none';
});

// === Options ===
document.getElementById('optVision')?.addEventListener('change', (e) => {
  document.getElementById('apiKeySection').style.display = e.target.checked ? 'block' : 'none';
});

// === Run Pipeline ===
document.getElementById('btnRun')?.addEventListener('click', async () => {
  if (!selectedPlan) return;

  // Switch to results page
  document.querySelectorAll('.nav-menu li').forEach(l => l.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-page="results"]').classList.add('active');
  document.getElementById('page-results').classList.add('active');

  document.getElementById('progressContainer').style.display = 'block';
  document.getElementById('resultsContainer').style.display = 'none';

  const formData = new FormData();
  formData.append('pdf', selectedPlan);

  try {
    const r = await fetch(`${API}/pipeline`, { method: 'POST', body: formData });
    const data = await r.json();
    currentJobId = data.job_id;
    pollStatus();
  } catch (err) {
    document.getElementById('progressLabel').textContent = `Erreur: ${err.message}`;
  }
});

function pollStatus() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    try {
      const r = await fetch(`${API}/status/${currentJobId}`);
      const data = await r.json();

      document.getElementById('progressLabel').textContent = data.progress || '...';
      const pct = data.status === 'done' ? 100 : data.status === 'running' ? 60 : 20;
      document.getElementById('progressPercent').textContent = pct + '%';
      document.getElementById('progressFill').style.width = pct + '%';

      // Update progress steps
      document.querySelectorAll('.progress-step').forEach(s => s.classList.remove('active', 'done'));

      if (data.status === 'done') {
        clearInterval(pollInterval);
        showResults(data);
      }
    } catch { /* retry */ }
  }, 1500);
}

function showResults(data) {
  document.getElementById('progressContainer').style.display = 'none';
  document.getElementById('resultsContainer').style.display = 'block';

  if (data.summary) {
    const grid = document.getElementById('summaryGrid');
    grid.innerHTML = '';
    const vols = data.summary.vols || {};
    for (const [k, v] of Object.entries(vols)) {
      grid.innerHTML += `<div class="summary-item"><span>${k}</span><strong>${typeof v === 'number' ? v.toFixed(1) : v}</strong></div>`;
    }
  }
}

// === Repos Page ===
function renderRepos() {
  const repos = {
    ferraillage: [
      { icon: 'fa-building', color: 'var(--accent-blue)', name: 'Armatures-Poteau-rectangulaire-BAEL', desc: 'Calcul ferraillage poteaux BAEL 91 — barres longues, cadres, épingles', status: 'active' },
      { icon: 'fa-ruler-combined', color: 'var(--accent-green)', name: 'calcul-section-acier-poutre-automatique-eurocode2', desc: 'Calcul sections acier poutres EC2', status: 'active' },
      { icon: 'fa-calculator', color: 'var(--accent-orange)', name: 'calcul-automatique-sections-acier-linteau-beton-arme', desc: 'Sections acier linteaux BA', status: 'active' },
      { icon: 'fa-circle-notch', color: 'var(--accent-cyan)', name: 'concrete-beam-diameters-quantities-reinforcement-Eurocode2', desc: 'Diamètres et quantités poutres EC2', status: 'active' },
      { icon: 'fa-shield-alt', color: 'var(--accent-purple)', name: 'Eurocode2-Concrete-Cover-Calc', desc: 'Calcul enrobage béton EC2', status: 'active' },
      { icon: 'fa-layer-group', color: 'var(--accent-red)', name: 'eurocode2-concrete-structural-class-calculator', desc: 'Classe structurale béton EC2', status: 'active' },
    ],
    vision: [
      { icon: 'fa-eye', color: 'var(--accent-purple)', name: 'GLM-OCR (zai-org)', desc: 'OCR open-source 0.9B — mode information extraction JSON strict', status: 'active' },
      { icon: 'fa-camera', color: 'var(--accent-cyan)', name: 'ConRebSeg (DTU-PAS)', desc: 'Segmentation ferraillage — datasets et modèles', status: 'config' },
      { icon: 'fa-database', color: 'var(--accent-orange)', name: 'synthetic-datasets-for-rebar', desc: 'Datasets synthétiques armatures', status: 'config' },
      { icon: 'fa-search', color: 'var(--accent-green)', name: 'RebarDSC', desc: 'Détection/comptage armatures', status: 'config' },
    ],
    takeoff: [
      { icon: 'fa-file-invoice', color: 'var(--accent-blue)', name: 'opentakeoff (Kentucky-ai)', desc: 'PDF takeoff engine piloté par agent MCP', status: 'active' },
      { icon: 'fa-cubes', color: 'var(--accent-green)', name: 'OpenConstructionERP', desc: 'BOQ, PDF/CAD/BIM takeoff, AI cost matching', status: 'config' },
      { icon: 'fa-lightbulb', color: 'var(--accent-orange)', name: 'DDC_Skills (221 skills)', desc: 'BIM, cost estimation, scheduling', status: 'config' },
      { icon: 'fa-code', color: 'var(--accent-cyan)', name: 'layerwise.ai', desc: 'API pipeline documentaire', status: 'config' },
    ],
    erp: [
      { icon: 'fa-tools', color: 'var(--accent-blue)', name: 'wall-load-bearing-calculation-tool', desc: 'Calcul murs porteurs', status: 'config' },
      { icon: 'fa-cogs', color: 'var(--accent-purple)', name: 'pypyBABA', desc: 'Modules Python BA (poutres, dalles, bielletirant, RDM)', status: 'active' },
    ],
  };

  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const tab = btn.dataset.tab;
      const list = repos[tab] || [];
      document.getElementById('reposContent').innerHTML = list.map(r => `
        <div class="repo-card">
          <div class="repo-icon" style="background:${r.color}"><i class="fas ${r.icon}"></i></div>
          <div class="repo-info">
            <h4>${r.name}</h4>
            <p>${r.desc}</p>
          </div>
          <span class="repo-badge ${r.status}">${r.status === 'active' ? 'Intégré' : 'Référence'}</span>
        </div>
      `).join('');
    });
  });

  // Trigger first tab
  document.querySelector('.tab-btn')?.click();
}

// === Settings ===
document.getElementById('openOutput')?.addEventListener('click', () => {
  const { shell } = require('electron');
  shell.showItemInFolder('output');
});

// === INSTALLER WIZARD ===
const COMPONENTS = [
  { id: "core", name: "Core Python", desc: "pdfplumber, openpyxl, PyMuPDF, reportlab", size: "~50 MB", required: true },
  { id: "api", name: "Backend API", desc: "FastAPI, uvicorn", size: "~30 MB", required: true },
  { id: "electron", name: "App Desktop Electron", desc: "Interface professionnelle", size: "~150 MB", required: true },
  { id: "vision", name: "Vision IA (torch)", desc: "transformers, torch, accelerate", size: "~2 GB", required: false },
  { id: "ocr", name: "GLM-OCR modèle", desc: "OCR local open-source", size: "~2 GB", required: false },
  { id: "latex", name: "LaTeX (TeX Live)", desc: "Rapports PDF avec formules", size: "~4 GB", required: false },
];

let installState = { step: 1, selected: ["core", "api", "electron"] };

function showInstallStep(n) {
  document.querySelectorAll('.installer-step-content').forEach(s => s.classList.remove('active'));
  document.getElementById(`install-step-${n}`).classList.add('active');
  document.querySelectorAll('.step-dot').forEach(d => {
    const s = parseInt(d.dataset.step);
    d.classList.remove('active', 'done');
    if (s === n) d.classList.add('active');
    if (s < n) d.classList.add('done');
  });
  installState.step = n;
}

function renderInstallComponents() {
  const container = document.getElementById('installComponents');
  if (!container) return;
  container.innerHTML = COMPONENTS.map(c => `
    <div class="component-item ${c.required ? 'required' : ''}">
      <label class="toggle">
        <input type="checkbox" id="comp_${c.id}" ${installState.selected.includes(c.id) ? 'checked' : ''} ${c.required ? 'disabled' : ''}>
        <span class="toggle-slider"></span>
      </label>
      <div class="component-info">
        <strong>${c.name} ${c.required ? '<span class="required">*</span>' : ''}</strong>
        <span>${c.desc}</span>
      </div>
      <span class="component-size">${c.size}</span>
    </div>
  `).join('');
  // Bind changes
  COMPONENTS.forEach(c => {
    const cb = document.getElementById(`comp_${c.id}`);
    cb?.addEventListener('change', () => {
      if (cb.checked && !installState.selected.includes(c.id)) installState.selected.push(c.id);
      else if (!cb.checked) installState.selected = installState.selected.filter(x => x !== c.id);
      updateInstallSummary();
    });
  });
  updateInstallSummary();
}

function updateInstallSummary() {
  let totalMB = 0;
  COMPONENTS.forEach(c => {
    if (installState.selected.includes(c.id)) {
      const mb = parseInt(c.size.replace(/[^0-9]/g, '')) || 0;
      totalMB += mb;
    }
  });
  const totalStr = totalMB > 1000 ? `~${(totalMB/1000).toFixed(1)} GB` : `~${totalMB} MB`;
  const el = document.getElementById('totalSize');
  if (el) el.textContent = totalStr;
}

// Installer navigation
document.querySelectorAll('.btn-next').forEach(btn => {
  btn.addEventListener('click', () => {
    const next = parseInt(btn.dataset.next);
    if (next === 3) {
      // Start installation
      showInstallStep(3);
      runInstallation();
    } else {
      showInstallStep(next);
    }
  });
});

document.querySelectorAll('.btn-prev').forEach(btn => {
  btn.addEventListener('click', () => {
    const prev = parseInt(btn.dataset.prev);
    showInstallStep(prev);
  });
});

// Render components when installer page is shown
document.querySelector('[data-page="installer"]')?.addEventListener('click', () => {
  renderInstallComponents();
  showInstallStep(1);
});

async function runInstallation() {
  const log = document.getElementById('installLog');
  const status = document.getElementById('installStatus');
  const bar = document.getElementById('installProgressBar');
  
  function logMsg(msg, type = 'info') {
    const div = document.createElement('div');
    div.className = `log-item log-${type}`;
    div.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
    log.appendChild(div);
    log.scrollTop = log.scrollHeight;
  }
  
  const total = installState.selected.length;
  
  for (let i = 0; i < installState.selected.length; i++) {
    const compId = installState.selected[i];
    const comp = COMPONENTS.find(c => c.id === compId);
    const pct = Math.round((i / total) * 100);
    bar.style.width = pct + '%';
    status.textContent = `Installation de ${comp.name}...`;
    logMsg(`Démarrage: ${comp.name}`);
    
    try {
      const r = await fetch(`${API}/install/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify([compId])
      });
      const data = await r.json();
      if (data.success?.includes(compId)) {
        logMsg(`${comp.name} installé avec succès`, 'success');
      } else {
        logMsg(`${comp.name}: ${data.failed?.[0]?.error || 'erreur'}`, 'error');
      }
    } catch (err) {
      logMsg(`Erreur réseau: ${err.message}`, 'error');
    }
  }
  
  bar.style.width = '100%';
  status.textContent = 'Installation terminée !';
  logMsg('Tous les composants sont installés.', 'success');
  
  document.getElementById('btnAfterInstall').disabled = false;
  document.querySelector('#install-step-3 .btn-prev').disabled = true;
}

document.getElementById('launchApp')?.addEventListener('click', () => {
  showInstallStep(4);
  // Switch to dashboard after delay
  setTimeout(() => {
    document.querySelectorAll('.nav-menu li').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.querySelector('[data-page="dashboard"]').classList.add('active');
    document.getElementById('page-dashboard').classList.add('active');
    renderDashboard();
  }, 1500);
});
