#!/bin/bash

# Fabric Endpoint Setup Script
# Script này sẽ setup và chạy Fabric endpoint service

set -e

echo "🚀 Fabric Endpoint Service Setup"
echo "================================="

# Kiểm tra Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker không được tìm thấy. Vui lòng cài đặt Docker trước."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose không được tìm thấy. Vui lòng cài đặt Docker Compose trước."
    exit 1
fi

echo "✅ Docker và Docker Compose đã sẵn sàng"

# Kiểm tra file .env
if [ ! -f .env ]; then
    echo "⚠️  File .env không tồn tại. Tạo từ env.example..."
    cp env.example .env
    echo "📝 Vui lòng chỉnh sửa file .env với API keys của bạn:"
    echo "   - OPENAI_API_KEY=your_key_here"
    echo "   - ANTHROPIC_API_KEY=your_key_here"  
    echo "   - GOOGLE_API_KEY=your_key_here"
    echo ""
    read -p "Nhấn Enter sau khi đã cấu hình .env file..."
fi

echo "✅ File .env đã tồn tại"

# Tạo network nếu chưa có
echo "🔧 Tạo Docker network..."
docker network create librechat-network 2>/dev/null || echo "Network librechat-network đã tồn tại"

# Build và start service
echo "🔨 Building Fabric endpoint service..."
docker-compose -f docker-compose.fabric.yml build

echo "🚀 Starting Fabric endpoint service..."
docker-compose -f docker-compose.fabric.yml up -d

# Đợi service start up
echo "⏳ Đợi service khởi động..."
sleep 10

# Health check
echo "🔍 Kiểm tra health của service..."
for i in {1..30}; do
    if curl -f http://localhost:8081/health >/dev/null 2>&1; then
        echo "✅ Fabric endpoint service đã sẵn sàng!"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "❌ Service không response sau 30 giây"
        echo "Kiểm tra logs:"
        docker-compose -f docker-compose.fabric.yml logs fabric-endpoint
        exit 1
    fi
    sleep 1
done

# Test API
echo "🧪 Testing API endpoints..."

echo "📋 Available patterns:"
curl -s http://localhost:8081/v1/patterns | jq '.patterns[]' 2>/dev/null || curl -s http://localhost:8081/v1/patterns

echo ""
echo "🎯 Available models:"
curl -s http://localhost:8081/v1/models | jq '.data[].id' 2>/dev/null || curl -s http://localhost:8081/v1/models

echo ""
echo "✅ Setup hoàn tất!"
echo ""
echo "📖 Thông tin service:"
echo "   - Health Check: http://localhost:8081/health"
echo "   - API Endpoint: http://localhost:8081/v1/"
echo "   - Available Patterns: http://localhost:8081/v1/patterns"
echo ""
echo "🔧 Để tích hợp với LibreChat:"
echo "   1. Đảm bảo cả LibreChat và Fabric service cùng network 'librechat-network'"
echo "   2. Trong librechat.yaml đã có cấu hình Fabric AI endpoint"
echo "   3. Restart LibreChat để load cấu hình mới"
echo ""
echo "📝 Commands hữu ích:"
echo "   - Xem logs: docker-compose -f docker-compose.fabric.yml logs -f"
echo "   - Stop service: docker-compose -f docker-compose.fabric.yml down"
echo "   - Restart: docker-compose -f docker-compose.fabric.yml restart"
echo ""
echo "🎉 Fabric endpoint service đã sẵn sàng để sử dụng!"
