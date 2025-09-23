# LibreChat MCP Servers

Thư mục này chứa các MCP (Model Context Protocol) servers tùy chỉnh cho LibreChat. Mỗi MCP server cung cấp các công cụ và khả năng đặc biệt để mở rộng tính năng của LibreChat.

## 📁 Available MCP Servers

### 🔬 Research AI Agent

**Folder**: `research-ai-agent/`  
**Transport**: SSE (Server-Sent Events)  
**Port**: 8000

Multi-agent system sử dụng LangGraph để thực hiện nghiên cứu chuyên sâu:

- **Research Agent**: Tìm kiếm và thu thập thông tin
- **Analysis Agent**: Phân tích dữ liệu và tìm patterns  
- **Synthesis Agent**: Tổng hợp và tạo báo cáo chuyên nghiệp

**Tools:**
- `research_comprehensive`: Nghiên cứu đầy đủ với multi-agent pipeline
- `research_quick`: Tìm kiếm nhanh với single agent

**Features:**
- ✅ Docker support
- ✅ SSE transport cho Docker environments
- ✅ Health monitoring
- ✅ Professional report generation
- ✅ Supports OpenAI & Anthropic models

---

### 🔄 Human in the Loop Agent

**Folder**: `human-in-loop-agent/`  
**Transport**: stdio (Standard I/O)  
**Dependencies**: Python stdlib only

Human-in-the-Loop workflows demonstrating AI workflows with human approval checkpoints:

- **Content Approval**: AI generates content → Human reviews → Approve/Edit/Reject
- **Task Planning**: AI creates plans → Human approves → Execute with modifications
- **Document Review**: AI analyzes docs → Human verifies → Final reviewed output

**Tools:**
- `start_content_approval`: Begin content generation workflow with human review
- `start_task_planning`: Start task breakdown workflow with human approval  
- `start_document_review`: Initiate document analysis with human verification
- `resume_workflow`: Continue paused workflow with human feedback
- `get_workflow_status`: Check status of running workflows
- `list_active_workflows`: Show all workflows awaiting human input

**Features:**
- ✅ Human approval gates at critical decision points
- ✅ Multi-stage workflow management
- ✅ State persistence during pauses
- ✅ Concurrent workflow support
- ✅ Simplified implementation (no external dependencies)
- ✅ Production-ready for LibreChat integration

**HIL Patterns Demonstrated:**
- 🔄 Interrupt & Resume: Pause workflows for human input
- 👥 Approval Gates: Critical decisions require human oversight
- ✏️ Iterative Editing: Human feedback improves AI output
- 📊 Workflow Management: Track and manage multiple HIL processes

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
cd mcps/research-ai-agent
./run_sse_server.sh docker
```

### Option 2: Local Development

```bash
cd mcps/research-ai-agent  
./run_sse_server.sh
```

## 🔧 LibreChat Configuration

Thêm vào `librechat.yaml`:

```yaml
mcpServers:
  research_ai_agent:
    type: sse
    url: http://host.docker.internal:8000/sse  # Docker Desktop
    # url: http://172.17.0.1:8000/sse         # Linux Docker
    # url: http://localhost:8000/sse          # Local
    timeout: 300000

endpoints:
  agents:
    capabilities: ["execute_code", "file_search", "actions", "tools"]
    recursionLimit: 50
```

## 📋 Development Guidelines

### Tạo MCP Server mới

1. **Tạo folder mới**: `mcps/your-server-name/`
2. **Required files**:
   ```
   your-server-name/
   ├── main.py              # Core MCP server
   ├── requirements.txt     # Dependencies
   ├── README.md           # Documentation
   ├── Dockerfile          # For Docker support
   ├── docker-compose.yml  # Docker orchestration
   ├── env.example         # Environment template
   └── test_server.py      # Testing script
   ```

3. **Transport support**:
   - **SSE**: Recommended cho Docker environments
   - **stdio**: For simple local development
   - **Both**: Maximum compatibility

4. **Health monitoring**:
   ```python
   @app.get("/health")
   async def health_check():
       return {"status": "healthy", "tools_count": len(tools)}
   ```

### Best Practices

- 🐳 **Docker First**: Design cho Docker deployment
- 🔍 **Health Checks**: Implement health endpoints
- 📝 **Documentation**: Comprehensive README với examples
- 🧪 **Testing**: Include test scripts
- 🔒 **Security**: Use environment variables cho sensitive data
- 📊 **Logging**: Implement proper logging với levels
- ⚡ **Performance**: Optimize cho production use

### Standard File Structure

```
mcps/
├── README.md                    # This file
├── server-name-1/
│   ├── main.py
│   ├── requirements.txt
│   ├── README.md
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── env.example
│   └── test_server.py
└── server-name-2/
    ├── main.py
    ├── requirements.txt
    └── ...
```

## 🔗 Useful Resources

- **MCP Specification**: https://modelcontextprotocol.io/
- **LibreChat Docs**: https://www.librechat.ai/docs/
- **LangGraph Docs**: https://langchain-ai.github.io/langgraph/
- **FastAPI Docs**: https://fastapi.tiangolo.com/

## 🤝 Contributing

1. Fork repository
2. Create MCP server trong `mcps/` folder
3. Follow development guidelines
4. Submit pull request với clear description
5. Include tests và documentation

---

**Happy Building! 🔧🤖**
