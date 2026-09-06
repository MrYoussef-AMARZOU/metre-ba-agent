// === Métré BA Agent — App Logic ===
const API = window.api ? null : 'http://127.0.0.1:8765';
let installed = {};
let addonsConfig = { required: {}, optional: {} };
let appUrl = null;

// ─── Navigation ───
function navigateTo(page) {
  document.querySelectorAll('.nav-menu li').forEach(l => l.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const navItem = document.querySelector(`[data-page="${page}"]`);
  const pageEl = document.getElementById('page-' + page);
  if (navItem) navItem.classList.add('active');
  if (pageEl) pageEl.classList.add('active');
}

document.querySelectorAll('.nav-menu li').forEach(li => {
  li.addEventListener('click', () => navigateTo(li.dataset.page));
});

// ─── Init ───
async function init() {
  // Get app URL from main process or use default
  try {
    if (window.api && window.api.getAppUrl) {
      appUrl = await window.api.getAppUrl();
    }
  } catch {}

  const baseUrl = appUrl || API;

  // Fetch addons status
  let retries = 0;
  while (retries < 5) {
    try {
      const r = await fetch(`${baseUrl}/addons`, { cache: 'no-store' });
      if (r.ok) {
        const data = await r.json();
        installed = data.installed || {};
        addonsConfig = data.config || {};
        break;
      }
    } catch (e) {}
    retries++;
    if (retries < 5) await new Promise(r => setTimeout(r, 1000));
  }

  updateDashboard();
  renderModules();
  renderAddons();
  renderSettings();
  renderRepos();
  setupUpload();
}

// ─── Dashboard ───
function updateDashboard() {
  const coreOk = installed.core !== false;
  const apiOk = installed.api !== false;
  const visionOk = installed.vision === true;
  const ocrOk = installed.ocr === true;

  document.getElementById('statAI').textContent = visionOk ? 'Actif' : '—';
  document.getElementById('statAI').style.color = visionOk ? 'var(--green)' : 'var(--text3)';

  const addonCount = Object.values(installed).filter(v => v).length;
  document.getElementById('statAddons').textContent = addonCount;
}

// ─── Modules ───
function renderModules() {
  const grid = document.getElementById('modulesGrid');
  if (!grid) return;

  const modules = [
    { icon: 'fa-ruler-combined', color: '#58a6ff', title: 'Métrique BA', desc: 'Extraction automatique des quantités de ferraillage', status: installed.core ? 'active' : 'config' },
    { icon: 'fa-eye', color: '#bc8cff', title: 'Vision IA', desc: 'Reconnaissance automatique des éléments sur plans', status: installed.vision ? 'active' : 'config' },
    { icon: 'fa-brain', color: '#39d2c0', title: 'GLM-OCR', desc: 'OCR local pour textes et annotations', status: installed.ocr ? 'active' : 'config' },
    { icon: 'fa-list-ol', color: '#d29922', title: 'BOQ / DPGF', desc: 'Gestion des devis quantitatifs détaillés', status: 'config' },
    { icon: 'fa-file-excel', color: '#3fb950', title: 'Rapports Excel', desc: 'Génération de métrés au format standard', status: installed.core ? 'active' : 'config' },
    { icon: 'fa-file-pdf', color: '#f85149', title: 'Rapports PDF', desc: 'Rapports détaillés avec formules BAEL', status: installed.core ? 'active' : 'config' },
  ];

  grid.innerHTML = modules.map(m => `
    <div class="module-card" onclick="navigateTo('metre')">
      <span class="module-badge ${m.status}">${m.status === 'active' ? 'Actif' : 'Disponible'}</span>
      <div class="module-icon" style="background:${m.color}"><i class="fas ${m.icon}"></i></div>
      <h4>${m.title}</h4>
      <p>${m.desc}</p>
    </div>
  `).join('');
}

// ─── Addons ───
function renderAddons() {
  const reqDiv = document.getElementById('addonsRequired');
  const optDiv = document.getElementById('addonsOptional');
  if (!reqDiv || !optDiv) return;

  const req = addonsConfig.required || {};
  const opt = addonsConfig.optional || {};

  reqDiv.innerHTML = Object.entries(req).map(([id, a]) => {
    const isInstalled = installed[id];
    const size = a.size_mb > 1000 ? `${(a.size_mb/1000).toFixed(1)} GB` : `${a.size_mb} MB`;
    return `
      <div class="addon-card ${isInstalled ? 'installed' : ''}">
        <div class="addon-icon" style="background:var(--blue)"><i class="fas fa-cube"></i></div>
        <div class="addon-info">
          <strong>${a.name}</strong>
          <span>${a.desc}</span>
          <span class="addon-size">~${size}</span>
        </div>
        <span class="badge ${isInstalled ? 'badge-green' : 'badge-red'}">${isInstalled ? 'Installé' : 'Manquant'}</span>
      </div>
    `;
  }).join('');

  optDiv.innerHTML = Object.entries(opt).map(([id, a]) => {
    const isInstalled = installed[id];
    const size = a.size_mb > 1000 ? `${(a.size_mb/1000).toFixed(1)} GB` : `${a.size_mb} MB`;
    return `
      <div class="addon-card ${isInstalled ? 'installed' : ''}">
        <div class="addon-icon" style="background:var(--purple)"><i class="fas fa-puzzle-piece"></i></div>
        <div class="addon-info">
          <strong>${a.name}</strong>
          <span>${a.desc}</span>
          <span class="addon-size">~${size}</span>
        </div>
        <span class="badge ${isInstalled ? 'badge-green' : 'badge-orange'}">${isInstalled ? 'Installé' : 'Optionnel'}</span>
      </div>
    `;
  }).join('');
}

// ─── Settings ───
function renderSettings() {
  const urlEl = document.getElementById('settingUrl');
  if (urlEl) urlEl.textContent = appUrl || API;

  const statusEl = document.getElementById('settingStatus');
  if (statusEl) {
    statusEl.textContent = 'Connecté';
    statusEl.className = 'badge badge-green';
  }

  const torchEl = document.getElementById('settingTorch');
  if (torchEl) {
    torchEl.textContent = installed.vision ? 'Installé' : 'Non installé';
    torchEl.className = `badge ${installed.vision ? 'badge-green' : 'badge-red'}`;
  }

  const ocrEl = document.getElementById('settingOCR');
  if (ocrEl) {
    ocrEl.textContent = installed.ocr ? 'Installé' : 'Non installé';
    ocrEl.className = `badge ${installed.ocr ? 'badge-green' : 'badge-red'}`;
  }

  const transformersEl = document.getElementById('settingTransformers');
  if (transformersEl) {
    transformersEl.textContent = installed.vision ? 'Installé' : 'Non installé';
    transformersEl.className = `badge ${installed.vision ? 'badge-green' : 'badge-red'}`;
  }
}

// ─── Repos ───
function renderRepos() {
  const grid = document.getElementById('reposGrid');
  if (!grid) return;

  const repos = [
    { name: 'BAEL 91 Poutres', desc: 'Calcul de section et d\'acier pour poutres BAEL', color: '#58a6ff' },
    { name: 'BAEL 91 Dalles', desc: 'Calcul de dalles en béton armé', color: '#3fb950' },
    { name: 'BAEL 91 Murs', desc: 'Calcul porteurs et non porteurs', color: '#d29922' },
    { name: 'BAEL 91 Colonnes', desc: 'Calcul de colonnes en compression', color: '#f85149' },
    { name: 'RebarDSC', desc: 'Reconnaissance de ferraillage par IA', color: '#bc8cff' },
    { name: 'GLM-OCR', desc: 'OCR open-source pour plans techniques', color: '#39d2c0' },
    { name: 'OpenConstructionERP', desc: 'ERP de construction open-source', color: '#58a6ff' },
    { name: 'pyBABA', desc: 'Reconnaissance de barres d\'acier', color: '#d29922' },
  ];

  grid.innerHTML = repos.map(r => `
    <div class="repo-card">
      <h4><i class="fas fa-code-branch" style="color:${r.color}"></i> ${r.name}</h4>
      <p>${r.desc}</p>
    </div>
  `).join('');
}

// ─── Upload ───
function setupUpload() {
  const zone = document.getElementById('uploadZone');
  const btn = document.getElementById('btnSelectPdf');
  const genBtn = document.getElementById('btnGenerate');

  if (!zone || !btn) return;

  // Drag & drop
  zone.addEventListener('dragover', (e) => { e.preventDefault(); zone.classList.add('dragover'); });
  zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));
  zone.addEventListener('drop', (e) => {
    e.preventDefault();
    zone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) handleFile(files[0]);
  });

  // Click to select
  btn.addEventListener('click', async (e) => {
    e.stopPropagation();
    if (window.api && window.api.selectPdf) {
      const filePath = await window.api.selectPdf();
      if (filePath) handleFile({ path: filePath, name: filePath.split(/[\\/]/).pop() });
    } else {
      const input = document.createElement('input');
      input.type = 'file';
      input.accept = '.pdf,.png,.jpg,.jpeg';
      input.onchange = (e) => { if (e.target.files[0]) handleFile(e.target.files[0]); };
      input.click();
    }
  });

  zone.addEventListener('click', () => btn.click());

  // Generate button click handler
  if (genBtn) {
    genBtn.addEventListener('click', () => startGeneration());
  }
}

function handleFile(file) {
  const zone = document.getElementById('uploadZone');
  const genBtn = document.getElementById('btnGenerate');

  // Show selected file
  const existing = zone.querySelector('.selected-file');
  if (existing) existing.remove();

  const div = document.createElement('div');
  div.className = 'selected-file';
  div.innerHTML = `<i class="fas fa-check-circle"></i> <strong>${file.name}</strong>`;
  zone.appendChild(div);

  // Enable generate button
  if (genBtn) genBtn.disabled = false;

  // Store file path
  zone.dataset.filePath = file.path || '';
}

// ─── Pipeline ───
async function startGeneration() {
  const zone = document.getElementById('uploadZone');
  const genBtn = document.getElementById('btnGenerate');
  const panel = document.getElementById('processingPanel');
  const steps = document.getElementById('processingSteps');
  const bar = document.getElementById('progressBar');
  
  if (!zone.dataset.filePath) {
    alert('Veuillez sélectionner un fichier PDF');
    return;
  }

  // Disable button, show processing
  genBtn.disabled = true;
  genBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Traitement...';
  panel.style.display = 'block';
  steps.innerHTML = '';
  bar.style.width = '0%';

  const baseUrl = appUrl || API;
  const useApi = window.api && window.api.uploadPdf;

  try {
    let jobId;
    
    if (useApi) {
      // Use Electron IPC
      jobId = await window.api.uploadPdf(zone.dataset.filePath);
    } else {
      // Use fetch API
      const formData = new FormData();
      const response = await fetch(zone.dataset.filePath);
      const blob = await response.blob();
      formData.append('pdf', blob, 'plan.pdf');
      
      const r = await fetch(`${baseUrl}/pipeline`, { method: 'POST', body: formData });
      const data = await r.json();
      jobId = data.job_id;
    }

    if (!jobId) throw new Error('Pas de job ID');
    
    addStep(steps, 'Job démarré: ' + jobId, 'success');
    bar.style.width = '10%';

    // Poll status
    await pollJobStatus(baseUrl, jobId, steps, bar);
    
  } catch (err) {
    addStep(steps, 'Erreur: ' + err.message, 'error');
    genBtn.disabled = false;
    genBtn.innerHTML = '<i class="fas fa-cogs"></i> Générer le Métré';
  }
}

async function pollJobStatus(baseUrl, jobId, steps, bar) {
  let done = false;
  let lastProgress = '';
  
  while (!done) {
    await new Promise(r => setTimeout(r, 1000));
    
    try {
      const r = await fetch(`${baseUrl}/status/${jobId}`);
      const data = await r.json();
      
      if (data.progress && data.progress !== lastProgress) {
        addStep(steps, data.progress, 'running');
        lastProgress = data.progress;
      }
      
      if (data.status === 'done') {
        bar.style.width = '100%';
        addStep(steps, 'Terminé ! Fichiers générés.', 'success');
        
        // Show download links
        if (data.outputs) {
          for (const [name, path] of Object.entries(data.outputs)) {
            addDownload(steps, name, `${baseUrl}/download/${jobId}/${name}`);
          }
        }
        
        done = true;
        const genBtn = document.getElementById('btnGenerate');
        genBtn.disabled = false;
        genBtn.innerHTML = '<i class="fas fa-cogs"></i> Générer le Métré';
        
      } else if (data.status === 'error') {
        addStep(steps, 'Erreur: ' + (data.error || 'Inconnue'), 'error');
        done = true;
        const genBtn = document.getElementById('btnGenerate');
        genBtn.disabled = false;
        genBtn.innerHTML = '<i class="fas fa-cogs"></i> Générer le Métré';
        
      } else {
        // Update progress bar
        const progress = parseInt(bar.style.width) || 10;
        if (progress < 90) bar.style.width = (progress + 5) + '%';
      }
    } catch (e) {
      // Retry
    }
  }
}

function addStep(container, text, type) {
  const div = document.createElement('div');
  div.className = 'step ' + type;
  div.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'times-circle' : 'spinner fa-spin'}"></i> ${text}`;
  container.appendChild(div);
}

function addDownload(container, name, url) {
  const div = document.createElement('div');
  div.className = 'step success';
  div.innerHTML = `<a href="${url}" target="_blank" style="color:var(--green)"><i class="fas fa-download"></i> ${name}</a>`;
  container.appendChild(div);
}

// ─── Backend status listeners ───
if (window.api && window.api.onApiReady) {
  window.api.onApiReady(() => {
    document.getElementById('statusDot').className = 'status-dot online';
    document.getElementById('statusText').textContent = 'Backend: connecté';
  });
}

if (window.api && window.api.onBackendStopped) {
  window.api.onBackendStopped(() => {
    document.getElementById('statusDot').className = 'status-dot offline';
    document.getElementById('statusText').textContent = 'Backend: déconnecté';
  });
}

// ─── IPC listeners from main process ───
if (window.api && window.api.onAppUrl) {
  window.api.onAppUrl((url) => { appUrl = url; });
}

// ─── Start ───
init();