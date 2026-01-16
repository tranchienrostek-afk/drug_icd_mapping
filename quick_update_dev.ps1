# PowerShell Quick Update Script (Code Only)
$ErrorActionPreference = "Stop"

$SERVER_IP = "10.14.190.28"
$SERVER_USER = "root"
$REMOTE_DIR = "/root/workspace/drug_icd_mapping"
$LOCAL_APP_DIR = "fastapi-medical-app"

function Invoke-Step {
    param([string]$Cmd)
    Write-Host "> $Cmd" -ForegroundColor DarkGray
    Invoke-Expression $Cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Command failed with exit code $LASTEXITCODE"
    }
}

Write-Host ">>> STARTING QUICK UPDATE (CODE ONLY) TO $SERVER_IP <<<" -ForegroundColor Green
Write-Host "Please have your SSH Password ready" -ForegroundColor Yellow

# 0. Check Connectivity
Write-Host "`n[0/3] Checking Connectivity..." -ForegroundColor Cyan
if (-not (Test-Connection -ComputerName $SERVER_IP -Count 1 -Quiet)) {
    Write-Error "Unable to reach $SERVER_IP. Please check your VPN."
}

# 1. Upload Code (Force Overwrite)
Write-Host "`n[1/3] Syncing Source Code..." -ForegroundColor Cyan
# Only upload code, skipping huge DB/venv folders if they exist locally in app dir
# We use scp -r which overwrites.
Invoke-Step "scp -o StrictHostKeyChecking=no -r $LOCAL_APP_DIR/* ${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/${LOCAL_APP_DIR}/"

# 2. Upload Env (In case config changed)
Write-Host "`n[2/3] Updating Environment..." -ForegroundColor Cyan
Invoke-Step "scp -o StrictHostKeyChecking=no $LOCAL_APP_DIR\.env.production ${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/${LOCAL_APP_DIR}/.env"

# 3. Remote Restart
Write-Host "`n[3/3] Rebuilding & Restarting Service..." -ForegroundColor Cyan
$REMOTE_SCRIPT = @"
set -e
cd ${REMOTE_DIR}/${LOCAL_APP_DIR}

# Ensure correct dockerfile
cp Dockerfile.prod Dockerfile

# Rebuild (Docker caches layers, so this is fast if only code changed)
export COMPOSE_PROJECT_NAME=drug_icd_mapping
export HOST_PORT=8006

echo 'Rebuilding...'
docker-compose up -d --build --no-deps app_medical_intel

echo 'Done. Status:'
docker-compose ps
"@

# Remove Carriage Returns (CR) for Linux compatibility
$REMOTE_SCRIPT = $REMOTE_SCRIPT -replace "`r", ""

ssh -t -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} "$REMOTE_SCRIPT"
if ($LASTEXITCODE -ne 0) { Write-Error "Remote command failed." }

Write-Host "`n>>> UPDATE COMPLETE <<<" -ForegroundColor Green
