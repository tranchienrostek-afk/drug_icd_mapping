#!/bin/bash
set -e

# ========================================
# PROMOTE STAGING TO PRODUCTION
# Chỉ deploy nếu staging đã pass test
# ========================================

# === Configuration ===
PROD_DIR="/root/workspace/drug_icd_mapping/fastapi-medical-app"
STAGING_LOG_DIR="/root/workspace/deploy_logs/staging"
PROD_LOG_DIR="/root/workspace/deploy_logs/production"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
LOG_FILE="${PROD_LOG_DIR}/${TIMESTAMP}.log"
BRANCH="main"

# === Colors ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# === Helper Functions ===
log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    log "${GREEN}✅ $1${NC}"
}

log_error() {
    log "${RED}❌ $1${NC}"
}

log_info() {
    log "${YELLOW}ℹ️  $1${NC}"
}

# === Pre-flight ===
echo "========================================"
echo "   🚀 PROMOTE TO PRODUCTION"
echo "   Time: $(date)"
echo "========================================"

mkdir -p "$PROD_LOG_DIR"

log "========================================"
log "PRODUCTION DEPLOYMENT STARTED"
log "========================================"

# === Step 1: Check staging passed ===
log_info "Step 1/5: Checking staging status..."

LAST_SUCCESS_FILE="${STAGING_LOG_DIR}/.last_success_commit"
if [ ! -f "$LAST_SUCCESS_FILE" ]; then
    log_error "No successful staging deployment found!"
    log_info "Please run deploy_staging.sh first and ensure tests pass."
    exit 1
fi

STAGING_COMMIT=$(cat "$LAST_SUCCESS_FILE")
log_success "Staging passed with commit: $STAGING_COMMIT"

# === Step 2: Pull code to production ===
log_info "Step 2/5: Updating production code..."
cd "$PROD_DIR"

# Backup current commit for rollback
CURRENT_PROD_COMMIT=$(git rev-parse --short HEAD)
echo "$CURRENT_PROD_COMMIT" > "${PROD_LOG_DIR}/.last_prod_commit"
log_info "Current prod commit (for rollback): $CURRENT_PROD_COMMIT"

git fetch origin 2>&1 | tee -a "$LOG_FILE"
git reset --hard origin/$BRANCH 2>&1 | tee -a "$LOG_FILE"
NEW_COMMIT=$(git rev-parse --short HEAD)

# Verify we're deploying the same commit that passed staging
if [ "$NEW_COMMIT" != "$STAGING_COMMIT" ]; then
    log_error "Commit mismatch!"
    log_error "Staging passed: $STAGING_COMMIT"
    log_error "Current HEAD: $NEW_COMMIT"
    log_info "New commits were pushed after staging. Please re-run staging first."
    exit 1
fi

log_success "Code updated to commit: $NEW_COMMIT"

# === Step 3: Check .env file ===
log_info "Step 3/5: Checking configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        cp .env.production .env
        log_info "Created .env from .env.production"
    else
        log_error ".env file not found!"
        exit 1
    fi
fi
log_success "Configuration OK"

# === Step 4: Deploy ===
log_info "Step 4/5: Deploying production..."

# Stop old container
docker-compose down 2>/dev/null || true
docker stop drug_icd_mapping_prod_web 2>/dev/null || true
docker rm drug_icd_mapping_prod_web 2>/dev/null || true

# Build and start
docker-compose build --no-cache 2>&1 | tee -a "$LOG_FILE"
docker-compose up -d 2>&1 | tee -a "$LOG_FILE"

log_success "Production container started on port 8000"

# === Step 5: Health Check ===
log_info "Step 5/5: Running health check..."
sleep 10

HEALTH_RESULT=$(curl -s http://localhost:8000/api/v1/health || echo "FAILED")
log "Health check result: $HEALTH_RESULT"

if echo "$HEALTH_RESULT" | grep -q "ok"; then
    log_success "Health check PASSED!"
    
    # Rename log to success
    SUCCESS_LOG="${PROD_LOG_DIR}/${TIMESTAMP}_DEPLOYED.log"
    mv "$LOG_FILE" "$SUCCESS_LOG"
    LOG_FILE="$SUCCESS_LOG"
    
    log ""
    log "========================================"
    log_success "PRODUCTION DEPLOYMENT SUCCESSFUL"
    log "Commit: $NEW_COMMIT"
    log "Log: $LOG_FILE"
    log "========================================"
    
    # Clear staging success marker
    rm -f "$LAST_SUCCESS_FILE"
    
    exit 0
else
    log_error "Health check FAILED!"
    
    # Rename log to failed
    FAILED_LOG="${PROD_LOG_DIR}/${TIMESTAMP}_FAILED.log"
    mv "$LOG_FILE" "$FAILED_LOG"
    LOG_FILE="$FAILED_LOG"
    
    log ""
    log "========================================"
    log_error "PRODUCTION DEPLOYMENT FAILED"
    log "Log: $LOG_FILE"
    log "========================================"
    log ""
    log_info "To rollback, run:"
    log_info "  cd $PROD_DIR"
    log_info "  git reset --hard $CURRENT_PROD_COMMIT"
    log_info "  docker-compose up -d --build"
    
    exit 1
fi
