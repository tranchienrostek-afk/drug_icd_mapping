#!/bin/bash
set -e

# ========================================
# SETUP STAGING ENVIRONMENT
# Chạy 1 lần để tạo staging folder
# ========================================

REPO_URL="https://github.com/tranchienrostek-afk/drug_icd_mapping.git"
STAGING_BASE="/root/workspace/drug_icd_mapping_staging"
LOG_DIR="/root/workspace/deploy_logs"

echo "========================================"
echo "   🔧 SETUP STAGING ENVIRONMENT"
echo "========================================"

# Create directories
echo "[1/4] Creating directories..."
mkdir -p "$STAGING_BASE"
mkdir -p "$LOG_DIR/staging"
mkdir -p "$LOG_DIR/production"
echo "✅ Directories created"

# Clone repository
echo ""
echo "[2/4] Cloning repository..."
if [ -d "$STAGING_BASE/.git" ]; then
    echo "⚠️  Repository already exists, pulling latest..."
    cd "$STAGING_BASE"
    git pull origin main
else
    git clone "$REPO_URL" "$STAGING_BASE"
fi
echo "✅ Repository ready"

# Setup .env
echo ""
echo "[3/4] Setting up configuration..."
cd "$STAGING_BASE/fastapi-medical-app"
if [ -f ".env.production" ]; then
    cp .env.production .env
    echo "✅ Created .env from template"
else
    echo "⚠️  No .env.production found, please create .env manually"
fi

# Make scripts executable
echo ""
echo "[4/4] Setting permissions..."
chmod +x scripts/deploy_staging.sh 2>/dev/null || true
chmod +x scripts/promote_to_prod.sh 2>/dev/null || true
echo "✅ Scripts are executable"

echo ""
echo "========================================"
echo "   ✅ STAGING SETUP COMPLETE"
echo "========================================"
echo ""
echo "Staging directory: $STAGING_BASE"
echo "Log directory: $LOG_DIR"
echo ""
echo "Next steps:"
echo "  1. Edit .env file if needed: nano $STAGING_BASE/fastapi-medical-app/.env"
echo "  2. Run staging deployment: $STAGING_BASE/fastapi-medical-app/scripts/deploy_staging.sh"
echo ""
