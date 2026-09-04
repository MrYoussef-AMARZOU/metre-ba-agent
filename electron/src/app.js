/* === Métré BA Agent — Electron UI === */

const API = 'http://127.0.0.1:8765';
let selectedFile = null;
let refFile = null;
let currentJobId = null;
let pollInterval = null;

// --- Navigation ---
document.querySelectorAll('.nav li').forEach(li => {
  li.addEventListener('click', () => {
    document.querySelectorAll('.nav li').forEach(l => l.classList.remove('active'));
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    li.classList.add('active');
    document.getElementById(`page-${li.dataset.page}`).classList.add('active');
  });
});

// --- API Status ---
async function checkApi() {
  try {
    const r = await fetch(`${API}/health`);
    const dot = document.querySelector('.status-dot');
    const txt = document.querySelector('.api-status span');
    if (r.ok) {
      dot.className = 'status-dot online';
      txt.textContent = 'Backend : en ligne';
    }
  } catch {
    setTimeout(checkApi, 2000);
  }
}
checkApi();

// --- File Upload ---
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', () => {
  if (fileInput.files.length) handleFile(fileInput.files[0]);
});

function handleFile(file) {
  selectedFile = file;
  document.getElementById('fileInfo').style.display = 'block';
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent = `${(file.size / 1024 / 1024).toFixed(1)} MB`;
  document.getElementById('runBtn').disabled = false;
  dropZone.style.display = 'none';
}

document.getElementById('removeFile').addEventListener('click', () => {
  selectedFile = null;
  document.getElementById('fileInfo').style.display = 'none';
  document.getElementById('runBtn').disabled = true;
  dropZone.style.display = 'flex';
});

// --- Reference file ---
document.getElementById('selectRef').addEventListener('click', async () => {
  const path = await window.api.selectXlsx();
  if (path) {
    refFile = path;
    document.getElementById('refName').textContent = path.split('\\').pop().split('/').pop();
  }
});

// --- Vision option ---
document.getElementById('optVision').addEventListener('change', (e) => {
  document.getElementById('apiKeyGroup').style.display = e.target.checked ? 'block' : 'none';
});

// --- Run Pipeline ---
document.getElementById('runBtn').addEventListener('click', async () => {
  if (!selectedFile) return;

  const btn = document.getElementById('runBtn');
  btn.querySelector('.btn-text').style.display = 'none';
  btn.querySelector('.btn-loading').style.display = 'inline-flex';
  btn.disabled = true;

  // Switch to results page
  document.querySelectorAll('.nav li').forEach(l => l.classList.remove('active'));
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelector('[data-page="results"]').classList.add('active');
  document.getElementById('page-results').classList.add('active');

  document.getElementById('progressBar').style.display = 'block';
  document.getElementById('resultsGrid').style.display = 'none';
  document.getElementById('summaryCard').style.display = 'none';
  document.getElementById('ecartsCard').style.display = 'none';

  // Build form data
  const formData = new FormData();
  formData.append('pdf', selectedFile);
  if (refFile) {
    const refBlob = await fetch(refFile).then(r => r.blob());
    formData.append('reference', refBlob, 'reference.xlsx');
  }
  const useVision = document.getElementById('optVision').checked;
  const useLatex = document.getElementById('optLatex').checked;
  if (useVision) {
    formData.append('api_key', document.getElementById('apiKey').value);
  }
  formData.append('latex', useLatex);

  try {
    const r = await fetch(`${API}/pipeline`, { method: 'POST', body: formData });
    const data = await r.json();
    currentJobId = data.job_id;
    pollStatus();
  } catch (err) {
    document.getElementById('progressText').textContent = `Erreur : ${err.message}`;
    btn.querySelector('.btn-text').style.display = 'inline';
    btn.querySelector('.btn-loading').style.display = 'none';
    btn.disabled = false;
  }
});

function pollStatus() {
  if (pollInterval) clearInterval(pollInterval);
  pollInterval = setInterval(async () => {
    try {
      const r = await fetch(`${API}/status/${currentJobId}`);
      const data = await r.json();

      document.getElementById('progressText').textContent = data.progress || '...';
      document.getElementById('progressFill').style.width =
        data.status === 'done' ? '100%' : data.status === 'running' ? '60%' : '20%';

      if (data.status === 'done') {
        clearInterval(pollInterval);
        showResults(data);
      } else if (data.status === 'error') {
        clearInterval(pollInterval);
        document.getElementById('progressText').textContent = `Erreur : ${data.error}`;
        document.getElementById('runBtn').querySelector('.btn-text').style.display = 'inline';
        document.getElementById('runBtn').querySelector('.btn-loading').style.display = 'none';
        document.getElementById('runBtn').disabled = false;
      }
    } catch { /* retry */ }
  }, 1500);
}

function showResults(data) {
  document.getElementById('progressBar').style.display = 'none';
  document.getElementById('resultsGrid').style.display = 'grid';
  document.getElementById('runBtn').querySelector('.btn-text').style.display = 'inline';
  document.getElementById('runBtn').querySelector('.btn-loading').style.display = 'none';
  document.getElementById('runBtn').disabled = false;

  // Summary
  if (data.summary) {
    document.getElementById('summaryCard').style.display = 'block';
    const grid = document.getElementById('summaryGrid');
    grid.innerHTML = '';
    const vols = data.summary.vols || {};
    for (const [k, v] of Object.entries(vols)) {
      grid.innerHTML += `<div class="summary-item"><span>${k}</span><strong>${typeof v === 'number' ? v.toFixed(1) : v}</strong></div>`;
    }
    if (data.summary.acier_total_kg) {
      grid.innerHTML += `<div class="summary-item"><span>Acier total</span><strong>${data.summary.acier_total_kg.toFixed(0)} kg</strong></div>`;
    }
  }

  // Download buttons
  const outputs = data.outputs || {};
  const dlMap = { 'dlExcel': 'metre_genere.xlsx', 'dlPdf': 'rapport_metre.pdf',
                  'dlLatex': 'rapport_metre_latex.pdf', 'dlOptim': 'optimisation.xlsx' };
  for (const [btnId, filename] of Object.entries(dlMap)) {
    const btn = document.getElementById(btnId);
    if (btn) {
      const url = `${API}/download/${currentJobId}/${filename}`;
      btn.onclick = () => {
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
      };
      btn.disabled = !outputs[filename];
    }
  }
}

// --- Settings ---
document.getElementById('optVision').addEventListener('change', (e) => {
  document.getElementById('apiKeyGroup').style.display = e.target.checked ? 'block' : 'none';
});
