#!/bin/bash
set -e

# ========================================
# Deploy Script for Drug ICD Mapping App
# ========================================

APP_DIR="/root/workspace/drug_icd_mapping/fastapi-medical-app"
BRANCH="main"

echo "========================================"
echo "   🚀 Auto Deploy Script"
echo "   Directory: $APP_DIR"
echo "========================================"

cd $APP_DIR

# 0. Pre-flight checks
echo ""
echo "[0/4] Pre-flight checks..."
echo "   - Disk usage: $(df -h / | tail -1 | awk '{print $5}')"
echo "   - Memory: $(free -h | grep Mem | awk '{print $3"/"$2}')"

# 1. Update Code
echo ""
echo "[1/4] Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/$BRANCH
echo "   ✅ Code updated"

# 2. Ensure .env exists
if [ ! -f .env ]; then
    echo ""
    echo "❌ ERROR: .env file not found!"
    echo "   Please create .env file first using .env.production template"
    exit 1
fi

# 3. Stop old container (ignore if not exists)
echo ""
echo "[2/4] Stopping old containers..."
docker-compose down 2>/dev/null || true
docker stop drug_icd_mapping_prod_web 2>/dev/null || true
docker rm drug_icd_mapping_prod_web 2>/dev/null || true
echo "   ✅ Old containers removed"

# 4. Build new image
echo ""
echo "[3/4] Building new Docker image..."
docker-compose build --no-cache
echo "   ✅ Image built"

# 5. Start service
echo ""
echo "[4/4] Starting service..."
docker-compose up -d

# 6. Health check
echo ""
echo "Waiting 10s for startup..."
sleep 10

echo ""
echo "========================================"
echo "   ✅ Deployment Complete!"
echo "========================================"
docker-compose ps

echo ""
echo "🔍 Health Check:"
curl -s http://localhost:8000/api/v1/health || echo "❌ Health check failed"
