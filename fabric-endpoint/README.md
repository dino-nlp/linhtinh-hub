# Fabric Endpoint Service

Service này cung cấp bridge giữa LibreChat và Fabric AI framework, cho phép sử dụng các Fabric patterns như một endpoint AI trong LibreChat.

## Tính năng

- 🧠 Tích hợp với Fabric AI patterns
- 🔄 Hỗ trợ streaming responses
- 📝 Nhiều patterns có sẵn (summarize, analyze_claims, extract_wisdom, v.v.)
- 🐳 Chạy độc lập trong Docker
- 🔌 Tương thích với LibreChat API

## Cài đặt và Chạy

### 1. Thiết lập Environment Variables

Tạo file `.env` trong thư mục này:

```bash
# AI Model API Keys (cần ít nhất một)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# Fabric Configuration (tùy chọn)
FABRIC_API_KEY=your_fabric_api_key_if_any
```

### 2. Build và Chạy Service

```bash
# Build và start service
docker-compose -f docker-compose.fabric.yml up -d --build

# Xem logs
docker-compose -f docker-compose.fabric.yml logs -f

# Stop service
docker-compose -f docker-compose.fabric.yml down
```

### 3. Kiểm tra Service

```bash
# Health check
curl http://localhost:8081/health

# Liệt kê models/patterns
curl http://localhost:8081/v1/models

# Test chat completion
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "fabric-summarize",
    "messages": [
      {
        "role": "user", 
        "content": "Hãy tóm tắt nội dung này: LibreChat là một nền tảng chat AI mã nguồn mở..."
      }
    ],
    "stream": false
  }'
```

## Patterns Có Sẵn

Service hỗ trợ các Fabric patterns sau:

- `fabric-analyze_claims` - Phân tích tính đúng/sai của các tuyên bố
- `fabric-extract_wisdom` - Trích xuất kiến thức từ nội dung
- `fabric-summarize` - Tóm tắt văn bản
- `fabric-improve_writing` - Cải thiện văn bản
- `fabric-translate` - Dịch ngôn ngữ
- `fabric-create_quiz` - Tạo câu hỏi trắc nghiệm
- `fabric-analyze_paper` - Phân tích paper khoa học
- `fabric-write_essay` - Viết bài luận
- Và nhiều patterns khác...

## API Endpoints

- `GET /health` - Health check
- `GET /v1/models` - Liệt kê tất cả models/patterns
- `POST /v1/chat/completions` - Chat completion (tương thích OpenAI API)
- `GET /v1/patterns` - Liệt kê patterns
- `POST /v1/patterns/{pattern_name}` - Thực thi pattern cụ thể

## Tích hợp với LibreChat

Sau khi service chạy, thêm vào `librechat.yaml`:

```yaml
endpoints:
  custom:
    - name: "Fabric AI"
      apiKey: "fabric-key"
      baseURL: "http://fabric-endpoint:8081/v1/"
      models:
        default: [
          "fabric-summarize",
          "fabric-analyze_claims", 
          "fabric-extract_wisdom",
          "fabric-improve_writing",
          "fabric-translate"
        ]
        fetch: false
      titleConvo: true
      titleModel: "fabric-summarize"
      titleMethod: "completion"
      forcePrompt: false
      userIdQuery: false
```

## Troubleshooting

### Service không start được
```bash
# Kiểm tra logs
docker-compose -f docker-compose.fabric.yml logs fabric-endpoint

# Kiểm tra port conflict
netstat -tulpn | grep 8081
```

### Fabric patterns không hoạt động
- Đảm bảo có ít nhất một AI API key được cấu hình
- Kiểm tra Fabric có được cài đặt đúng trong container
- Xem logs để kiểm tra lỗi Fabric CLI

### Kết nối từ LibreChat bị lỗi
- Đảm bảo cả LibreChat và Fabric service cùng network
- Kiểm tra baseURL trong librechat.yaml đúng
- Verify health endpoint: `curl http://fabric-endpoint:8081/health`

## Development

Để phát triển và debug:

```bash
# Chạy local development mode
export OPENAI_API_KEY=your_key
python3 fabric_service.py

# Test với curl
curl -X POST http://localhost:8081/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "fabric-summarize",
    "messages": [{"role": "user", "content": "Test message"}]
  }'
```

## Cấu hình Nâng cao

### Custom Patterns
Để thêm custom patterns, mount thư mục patterns:

```yaml
volumes:
  - ./custom-patterns:/home/fabricuser/.config/fabric/patterns
```

### Memory và CPU Limits
```yaml
services:
  fabric-endpoint:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '0.5'
```
