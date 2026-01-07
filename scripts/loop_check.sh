# Script kiểm tra nhanh (Test + Lint)
#!/bin/bash
# Chạy loop kiểm tra nhanh
echo "🚀 STARTING EDIT-TEST LOOP CHECK..."

# 1. Chạy Test (Dừng ngay nếu lỗi)
pytest $1 -v --maxfail=1
if [ $? -ne 0 ]; then
    echo "❌ TEST FAILED. Fix code logic immediately."
    exit 1
fi

echo "✅ TEST PASSED. Ready to Refactor or Commit."