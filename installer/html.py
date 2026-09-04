# === Installer Wizard — Installation pas à pas ===
# Étapes : Bienvenue → Choix addons → Installation → Configuration → Terminé

WELCOME_HTML = """
<div class="install-welcome">
  <div class="install-logo">
    <i class="fas fa-building"></i>
  </div>
  <h1>Métré BA Agent</h1>
  <p class="version">Version 1.0.0</p>
  <p class="welcome-text">
    Bienvenue dans l'installation de <strong>Métré BA Agent</strong>.<br>
    Cet assistant va installer les composants nécessaires pour générer<br>
    des métrés béton armé à partir de plans PDF/AutoCAD.
  </p>
  <div class="install-features">
    <div class="feature"><i class="fas fa-file-excel"></i> Métré Excel professionnel</div>
    <div class="feature"><i class="fas fa-brain"></i> Vision IA + OCR local</div>
    <div class="feature"><i class="fas fa-file-pdf"></i> Rapports PDF + LaTeX</div>
    <div class="feature"><i class="fas fa-cubes"></i> 16 modules BAEL/EC2 intégrés</div>
  </div>
</div>
"""

COMPONENTS_HTML = """
<div class="install-components">
  <h2><i class="fas fa-puzzle-piece"></i> Choix des composants</h2>
  <p>Sélectionnez les addons à installer. Les composants marqués <span class="required">*</span> sont obligatoires.</p>
  
  <div class="components-list">
    <div class="component-item required">
      <label class="toggle">
        <input type="checkbox" id="compCore" checked disabled>
        <span class="toggle-slider"></span>
      </label>
      <div class="component-info">
        <strong>Core Python <span class="required">*</span></strong>
        <span>pdfplumber, openpyxl, PyMuPDF, PyYAML, reportlab (~50MB)</span>
      </div>
      <span class="component-size">~50 MB</span>
    </div>
    
    <div class="component-item required">
      <label class="toggle">
        <input type="checkbox" id="compApi" checked>
        <span class="toggle-slider"></span>
      </label>
      <div class="component-info">
        <strong>Backend API <span class="required">*</span></strong>
        <span>FastAPI, uvicorn, python-multipart (~30MB)</span>
      </div>
      <span class="component-size">~30 MB</span>
    </div>
    
    <div class="component-item required">
      <label class="toggle">
        <input type="checkbox" id="compElectron" checked>
        <span class="toggle-slider"></span>
      </label>
      <div class="component-info">
        <strong>Application Desktop Electron <span class="required">*</span></strong>
        <span>Interface professionnelle (~150MB)</span>
      </div>
      <span class="component-size">~150 MB</span>
    </div>
    
    <div class="component-item">
      <label class="toggle">
        <input type="checkbox" id="compVision">
        <span class="toggle-slider"></span>
      </label>
      <div class="component-info">
        <strong>Vision IA (transformers + torch)</strong>
        <span>Extraction automatique poteaux/CH/LG/poutres (~2GB)</span>
      </div>
      <span class="component-size">~2 GB</span>
    </div>
    
    <div class="component-item">
      <label class="toggle">
        <input type="checkbox" id="compOcr">
        <span class="toggle-slider"></span>
      </label>
      <div class="component-info">
        <strong>GLM-OCR modèle</strong>
        <span>OCR local open-source pour plans scannés (~2GB)</span>
      </div>
      <span class="component-size">~2 GB</span>
    </div>
    
    <div class="component-item">
      <label class="toggle">
        <input type="checkbox" id="compLatex">
        <span class="toggle-slider"></span>
      </label>
      <div class="component-info">
        <strong>LaTeX (TeX Live)</strong>
        <span>Génération rapports PDF avec formules (~4GB)</span>
      </div>
      <span class="component-size">~4 GB</span>
    </div>
  </div>
  
  <div class="install-summary">
    <strong>Espace disque estimé : <span id="totalSize">~230 MB</span></strong>
    <span>Temps estimé : <span id="totalTime">~5 min</span></span>
  </div>
</div>
"""

INSTALLING_HTML = """
<div class="install-progress">
  <h2><i class="fas fa-download"></i> Installation en cours</h2>
  <p id="installStatus">Préparation...</p>
  
  <div class="progress-bar-container">
    <div class="progress-bar-fill" id="installProgressBar"></div>
  </div>
  
  <div class="install-log" id="installLog"></div>
</div>
"""

CONFIG_HTML = """
<div class="install-config">
  <h2><i class="fas fa-cog"></i> Configuration</h2>
  <p>Paramétrez l'application (vous pourrez modifier plus tard).</p>
  
  <div class="config-field">
    <label>Clé API Anthropic (optionnel)</label>
    <input type="password" id="configApiKey" placeholder="sk-ant-..." class="form-input">
    <span class="field-hint">Nécessaire uniquement pour la Vision IA. GLM-OCR fonctionne sans clé.</span>
  </div>
  
  <div class="config-field">
    <label>Dossier de sortie</label>
    <div class="input-row">
      <input type="text" id="configOutput" value="output" class="form-input">
      <button class="btn btn-outline" id="browseOutput"><i class="fas fa-folder-open"></i></button>
    </div>
  </div>
  
  <div class="config-field">
    <label>Langue des rapports</label>
    <select id="configLang" class="form-input">
      <option value="fr" selected>Français</option>
      <option value="ar">العربية</option>
      <option value="en">English</option>
    </select>
  </div>
</div>
"""

DONE_HTML = """
<div class="install-done">
  <div class="done-icon"><i class="fas fa-check-circle"></i></div>
  <h2>Installation terminée !</h2>
  <p>Métré BA Agent est prêt à l'emploi.</p>
  
  <div class="done-actions">
    <button class="btn btn-primary btn-lg" id="launchApp">
      <i class="fas fa-rocket"></i> Lancer l'application
    </button>
    <button class="btn btn-outline" id="openFolder">
      <i class="fas fa-folder-open"></i> Ouvrir le dossier
    </button>
  </div>
  
  <div class="done-info">
    <p><strong>Prochaines étapes :</strong></p>
    <ul>
      <li>Importez un plan PDF via l'onglet "Nouveau Métré"</li>
      <li>Ajoutez un métré de référence pour la comparaison</li>
      <li>Lancez le pipeline et téléchargez les résultats</li>
    </ul>
  </div>
</div>
"""
