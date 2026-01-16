# PowerShell Deployment Script for Task 024
$ErrorActionPreference = "Stop"

$SERVER_IP = "10.14.190.28"
$SERVER_USER = "root"
$REMOTE_DIR = "/root/workspace/drug_icd_mapping"
$LOCAL_APP_DIR = "fastapi-medical-app"
$LOCAL_DB_PATH = "fastapi-medical-app\app\database\medical.db"

function Run-Exec {
    param([string]$Cmd)
    Write-Host "> $Cmd" -ForegroundColor DarkGray
    Invoke-Expression $Cmd
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Command failed with exit code $LASTEXITCODE"
    }
}

Write-Host ">>> STARTING DEPLOYMENT TO $SERVER_IP <<<" -ForegroundColor Green
Write-Host "Please have your SSH Password ready" -ForegroundColor Yellow

# 0. Check Connectivity
Write-Host "`n[0/4] Checking Connectivity..." -ForegroundColor Cyan
if (-not (Test-Connection -ComputerName $SERVER_IP -Count 1 -Quiet)) {
    Write-Error "Unable to reach $SERVER_IP. Please check your VPN network connection."
}

# 1. Check DB File
if (-not (Test-Path $LOCAL_DB_PATH)) {
    Write-Error "Database file not found at $LOCAL_DB_PATH"
}

# 1.5. Prepare Remote Directories (Fix for "No such file or directory")
Write-Host "`n[1.5/4] Creating Remote Directories..." -ForegroundColor Cyan
Run-Exec "ssh -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} 'mkdir -p ${REMOTE_DIR}/data ${REMOTE_DIR}/${LOCAL_APP_DIR}'"

# 2. Upload Code
Write-Host "`n[1/4] Uploading Source Code..." -ForegroundColor Cyan
# Copy content of local app dir TO remote app dir
Run-Exec "scp -o StrictHostKeyChecking=no -r $LOCAL_APP_DIR/* ${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/${LOCAL_APP_DIR}/"

# 3. Upload Data
Write-Host "`n[2/4] Uploading Database..." -ForegroundColor Cyan
Run-Exec "scp -o StrictHostKeyChecking=no $LOCAL_DB_PATH ${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/data/medical.db"

# 4. Upload Env
Write-Host "`n[3/4] Configuring Environment..." -ForegroundColor Cyan
Run-Exec "scp -o StrictHostKeyChecking=no $LOCAL_APP_DIR\.env.production ${SERVER_USER}@${SERVER_IP}:${REMOTE_DIR}/${LOCAL_APP_DIR}/.env"

# 5. Remote Commands (Build & Up)
Write-Host "`n[4/4] Executing Remote Build & Start..." -ForegroundColor Cyan
$REMOTE_SCRIPT = @"
# Strict Mode
set -e

cd ${REMOTE_DIR}/${LOCAL_APP_DIR}

# Ensure data permissions
mkdir -p ../data
chmod -R 777 ../data

# Check logic for port
echo 'Checking ports...'
netstat -tulpn | grep :800 || echo 'Port 800X looks clean'

export COMPOSE_PROJECT_NAME=drug_icd_mapping
export HOST_PORT=8006 # DYNAMICALLY CHOSEN

echo 'Deploying to Port' \$HOST_PORT

# Use Prod Dockerfile
cp Dockerfile.prod Dockerfile

# Build & Up Specific Service
docker-compose up -d --build --no-deps app_medical_intel

echo 'Deployment Complete. Checking Status...'
docker-compose ps
"@

# Remove Carriage Returns (CR) for Linux compatibility
$REMOTE_SCRIPT = $REMOTE_SCRIPT -replace "`r", ""

# Execute via SSH
ssh -t -o StrictHostKeyChecking=no ${SERVER_USER}@${SERVER_IP} "$REMOTE_SCRIPT"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Remote SSH command failed."
}

Write-Host "`n>>> DEPLOYMENT SUCCESSFUL <<<" -ForegroundColor Green
Write-Host "API Health Check: http://${SERVER_IP}:8006/api/v1/health"
