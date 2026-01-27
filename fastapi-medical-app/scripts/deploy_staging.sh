#!/bin/bash
set -e

# ========================================
# STAGING DEPLOYMENT SCRIPT
# Tự động: Pull → Build → Test → Log
# ========================================

# === Configuration ===
STAGING_DIR="/root/workspace/drug_icd_mapping_staging/fastapi-medical-app"
LOG_DIR="/root/workspace/deploy_logs/staging"
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
LOG_FILE="${LOG_DIR}/${TIMESTAMP}.log"
BRANCH="main"

# === Colors for terminal ===
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
echo "   🚀 STAGING DEPLOYMENT"
echo "   Time: $(date)"
echo "========================================"

# Create log directory if not exists
mkdir -p "$LOG_DIR"

log "========================================"
log "STAGING DEPLOYMENT STARTED"
log "Branch: $BRANCH"
log "Directory: $STAGING_DIR"
log "========================================"

# === Step 1: Check staging directory exists ===
log_info "Step 1/5: Checking staging directory..."
if [ ! -d "$STAGING_DIR" ]; then
    log_error "Staging directory not found: $STAGING_DIR"
    log_info "Please run setup_staging.sh first to create staging environment"
    exit 1
fi
log_success "Staging directory exists"

# === Step 2: Pull latest code ===
log_info "Step 2/5: Pulling latest code from GitHub..."
cd "$STAGING_DIR"
git fetch origin 2>&1 | tee -a "$LOG_FILE"
git reset --hard origin/$BRANCH 2>&1 | tee -a "$LOG_FILE"
COMMIT_HASH=$(git rev-parse --short HEAD)
log_success "Code updated to commit: $COMMIT_HASH"

# === Step 3: Check .env file ===
log_info "Step 3/5: Checking configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.production" ]; then
        cp .env.production .env
        log_info "Created .env from .env.production template"
    else
        log_error ".env file not found!"
        exit 1
    fi
fi
log_success "Configuration OK"

# === Step 4: Build and Start Container ===
log_info "Step 4/5: Building Docker image..."
docker-compose -f docker-compose.staging.yml down 2>/dev/null || true
docker-compose -f docker-compose.staging.yml build --no-cache 2>&1 | tee -a "$LOG_FILE"
docker-compose -f docker-compose.staging.yml up -d 2>&1 | tee -a "$LOG_FILE"
log_success "Container started on port 8001"

# Wait for container to be ready
log_info "Waiting 15s for container startup..."
sleep 15

# === Step 5: Run Unit Tests ===
log_info "Step 5/5: Running unit tests..."
log ""
log "--- UNITTEST OUTPUT ---"

TEST_OUTPUT=$(docker exec drug_icd_staging_web pytest unittest/ -v --tb=short 2>&1) || TEST_EXIT_CODE=$?
echo "$TEST_OUTPUT" | tee -a "$LOG_FILE"
log "--- END UNITTEST OUTPUT ---"
log ""

# Check test result
if [ "${TEST_EXIT_CODE:-0}" -eq 0 ]; then
    log_success "All tests PASSED!"
    
    # Rename log file to indicate success
    SUCCESS_LOG="${LOG_DIR}/${TIMESTAMP}_SUCCESS.log"
    mv "$LOG_FILE" "$SUCCESS_LOG"
    LOG_FILE="$SUCCESS_LOG"
    
    log ""
    log "========================================"
    log_success "STAGING DEPLOYMENT SUCCESSFUL"
    log "Commit: $COMMIT_HASH"
    log "Log: $LOG_FILE"
    log "========================================"
    log ""
    log_info "Ready to promote to production!"
    log_info "Run: ./promote_to_prod.sh"
    
    # Create a marker file for promote script
    echo "$COMMIT_HASH" > "${LOG_DIR}/.last_success_commit"
    
    exit 0
else
    log_error "Tests FAILED!"
    
    # Rename log file to indicate failure
    FAILED_LOG="${LOG_DIR}/${TIMESTAMP}_FAILED.log"
    mv "$LOG_FILE" "$FAILED_LOG"
    LOG_FILE="$FAILED_LOG"
    
    log ""
    log "========================================"
    log_error "STAGING DEPLOYMENT FAILED"
    log "Commit: $COMMIT_HASH"
    log "Log: $LOG_FILE"
    log "========================================"
    log ""
    log_info "Please check the log file for details."
    log_info "Staging container is still running for debugging."
    log_info "Access: http://localhost:8001"
    
    exit 1
fi
