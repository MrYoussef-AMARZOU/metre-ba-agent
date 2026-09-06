@echo off
title Métré BA Agent
cd /d "%~dp0"

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
    pip install pdfplumber PyMuPDF openpyxl PyYAML reportlab fastapi uvicorn python-multipart >nul 2>&1
    echo. > .deps_installed
    echo OK.
)

REM Installer les dépendances Electron si nécessaire
if not exist "electron\node_modules" (
    echo Installation des dépendances Electron...
    cd electron && npm install && cd ..
    echo OK.
)

echo.
echo Démarrage du backend...

REM Tuer ancien processus
taskkill /f /im python.exe >nul 2>&1
timeout /t 1 /nobreak >nul

REM Lancer le backend en arrière-plan (fenêtre cachée)
start "" /min cmd /c "cd /d "%~dp0backend" && python -m uvicorn api:app --host 127.0.0.1 --port 8765"

REM Attendre que le backend soit prêt
echo Attente du backend...
set /a count=0
:waitloop
timeout /t 1 /nobreak >nul
set /a count+=1
curl -s http://127.0.0.1:8765/health >nul 2>&1
if errorlevel 1 (
    if %count% lss 15 goto waitloop
    echo ERREUR: Backend non démarré après 15 secondes
    pause
    exit /b 1
)
echo Backend prêt.

echo.
echo Démarrage de l'app Electron...
cd electron
npm start
cd ..

echo.
echo Arrêt du backend...
taskkill /f /im python.exe >nul 2>&1
echo Terminé.
pause