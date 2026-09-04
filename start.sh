#!/bin/bash
# === Métré BA Agent — Démarrage complet (Linux/Mac) ===

set -e
echo ""
echo "========================================"
echo "  Métré BA Agent — Démarrage"
echo "========================================"
echo ""

# Vérifier Python
command -v python3 >/dev/null 2>&1 || { echo "ERREUR: Python3 non trouvé"; exit 1; }

# Vérifier Node.js
command -v node >/dev/null 2>&1 || { echo "ERREUR: Node.js non trouvé"; exit 1; }

# Installer les dépendances Python si nécessaire
if [ ! -f ".deps_installed" ]; then
    echo "Installation des dépendances Python..."
    pip3 install -r requirements.txt fastapi uvicorn python-multipart 2>/dev/null
    touch .deps_installed
fi

# Installer les dépendances Electron si nécessaire
if [ ! -d "electron/node_modules" ]; then
    echo "Installation des dépendances Electron..."
    cd electron && npm install && cd ..
fi

echo ""
echo "Démarrage du backend Python (port 8765)..."
python3 -m uvicorn backend.api:app --host 127.0.0.1 --port 8765 &
BACKEND_PID=$!

echo "Démarrage de l'app Electron..."
cd electron && npm start
cd ..

echo ""
echo "Arrêt du backend..."
kill $BACKEND_PID 2>/dev/null
echo "Terminé."
