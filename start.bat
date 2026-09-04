@echo off
REM === Métré BA Agent — Démarrage complet (Windows) ===
REM Lance le backend Python + l'app Electron

echo.
echo ========================================
echo   Métré BA Agent — Démarrage
echo ========================================
echo.

REM Vérifier Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python non trouvé. Installez Python 3.10+
    pause
    exit /b 1
)

REM Vérifier Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Node.js non trouvé. Installez Node.js 18+
    pause
    exit /b 1
)

REM Installer les dépendances Python si nécessaire
if not exist ".deps_installed" (
    echo Installation des dépendances Python...
    pip install -r requirements.txt fastapi uvicorn python-multipart 2>nul
    echo. > .deps_installed
)

REM Installer les dépendances Electron si nécessaire
if not exist "electron\node_modules" (
    echo Installation des dépendances Electron...
    cd electron
    npm install
    cd ..
)

echo.
echo Démarrage du backend Python (port 8765)...
start /b python -m uvicorn backend.api:app --host 127.0.0.1 --port 8765

echo Démarrage de l'app Electron...
cd electron
npm start
cd ..

echo.
echo Arrêt du backend...
taskkill /f /im python.exe >nul 2>&1
echo Terminé.
