param(
    [string]$TargetDestination = "C:\PlanBA_Deployment_Share"
)

$ErrorActionPreference = "Stop"

# 0. Fermeture des instances actives
taskkill /F /IM PlanBA_Metre_Extractor.exe 2>$null
Start-Sleep -Seconds 1

$SourceDir = "C:\PlanBA_App\PlanBA_Metre_Extractor"
$RemoteExtractPath = Join-Path $TargetDestination "PlanBA_Metre_Extractor"

Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "  PLANBA -- Déploiement vers $TargetDestination" -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

# 1. Vérification source
if (-not (Test-Path "$SourceDir\PlanBA_Metre_Extractor.exe")) {
    Write-Host "❌ Erreur : L'exécutable source est introuvable dans : $SourceDir" -ForegroundColor Red
    exit 1
}

try {
    # 2. Préparation du dossier cible
    Write-Host "`n[1/2] Connexion et préparation du dossier cible..." -ForegroundColor Yellow
    if (-not (Test-Path $RemoteExtractPath)) {
        New-Item -ItemType Directory -Force -Path $RemoteExtractPath | Out-Null
    } else {
        Remove-Item "$RemoteExtractPath\*" -Recurse -Force -ErrorAction SilentlyContinue
    }

    # 3. Copie des fichiers
    Write-Host "`n[2/2] Transfert des fichiers de l'application (312 Mo)..." -ForegroundColor Yellow
    Copy-Item "$SourceDir\*" -Destination $RemoteExtractPath -Recurse -Force

    Write-Host "`n====================================================" -ForegroundColor Cyan
    Write-Host "  ✅ DÉPLOIEMENT TERMINÉ AVEC SUCCÈS !" -ForegroundColor Green
    Write-Host "  Dossier opérationnel : $RemoteExtractPath" -ForegroundColor Cyan
    Write-Host "====================================================" -ForegroundColor Cyan
}
catch {
    Write-Host "`n====================================================" -ForegroundColor Red
    Write-Host "  ❌ ÉCHEC DU DÉPLOIEMENT" -ForegroundColor Red
    Write-Host "  Cause : $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "====================================================" -ForegroundColor Red
    exit 1
}
