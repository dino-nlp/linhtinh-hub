# Fabric API Service

OpenAI-compatible API for Fabric integration with LibreChat using Langchain/Langgraph.

## Overview

This service provides an OpenAI-compatible API endpoint that integrates with Fabric, a command-line tool for processing text using various patterns. The service uses Langchain for tool wrapping and Langgraph for workflow orchestration.

## Features

- OpenAI-compatible API endpoints (`/v1/models` and `/v1/chat/completions`)
- Support for 5 key Fabric patterns:
  - Summarize
  - Analyze claims
  - Extract wisdom
  - Improve writing
  - Translate
- Both streaming and non-streaming responses
- Authentication via API keys
- Docker support for easy deployment

## Architecture

The service is built with the following components:

1. **FabricIntegrationLayer**: Handles communication with the Fabric CLI/API
2. **FabricTools**: Langchain tool wrappers for each Fabric pattern
3. **FabricWorkflow**: Langgraph workflow for pattern execution
4. **FastAPI Application**: Provides OpenAI-compatible API endpoints

## Installation

### Prerequisites

- Python 3.11 or higher
- Fabric CLI installed and accessible in PATH
- OpenAI API key

### Local Development

1. Clone the repository
2. Navigate to the `endpoint_services/fabric` directory
3. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
5. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```
6. Edit the `.env` file with your configuration
7. Run the application:
   ```bash
   python -m app.main
   ```

### Docker Deployment

1. Build the Docker image:
   ```bash
   docker-compose build
   ```
2. Run the container:
   ```bash
   docker-compose up -d
   ```

## API Usage

### Authentication

All API requests must include an API key in the `Authorization` header:

```
Authorization: Bearer your_api_key
```

### Endpoints

#### List Models

```bash
curl -X GET http://localhost:8000/v1/models \
  -H "Authorization: Bearer your_api_key"
```

#### Chat Completion

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "model": "fabric",
    "messages": [
      {"role": "user", "content": "Summarize this text: The quick brown fox jumps over the lazy dog."}
    ]
  }'
```

#### Streaming Chat Completion

```bash
curl -X POST http://localhost:8000/v1/chat/completions/stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_key" \
  -d '{
    "model": "fabric",
    "messages": [
      {"role": "user", "content": "Summarize this text: The quick brown fox jumps over the lazy dog."}
    ],
    "stream": true
  }'
```

#### Get Fabric Patterns

```bash
curl -X GET http://localhost:8000/v1/fabric/patterns \
  -H "Authorization: Bearer your_api_key"
```

#### Get Fabric Tools

```bash
curl -X GET http://localhost:8000/v1/fabric/tools \
  -H "Authorization: Bearer your_api_key"
```

## Integration with LibreChat

To integrate this service with LibreChat:

1. Deploy the Fabric API service
2. Configure LibreChat to use the service as an endpoint
3. Update LibreChat's configuration to include the Fabric model

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black app/
isort app/
flake8 app/
mypy app/
```

## License

This project is part of LibreChat and is licensed under the same terms.