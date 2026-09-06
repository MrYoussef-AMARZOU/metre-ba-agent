# === Métré BA Agent — Launch (silencieux) ===
$root = "C:\Users\youss\OneDrive\Desktop\Yoyo\metre-ba-agent"

# Kill old processes
Get-Process python, electron, node -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Start backend (hidden)
Start-Process python -ArgumentList "-m", "uvicorn", "backend.api:app", "--host", "127.0.0.1", "--port", "8765" -WorkingDirectory $root -WindowStyle Hidden

# Wait for backend
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:8765/health" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
        if ($r.StatusCode -eq 200) { break }
    } catch {}
}

# Start Electron (using npm start)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\electron'; npm start" -WindowStyle Hidden