import logging
from typing import Dict, Any, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from ..core.fabric_integration import FabricIntegrationLayer
from ..workflows.fabric_workflow import FabricWorkflow

logger = logging.getLogger(__name__)

router = APIRouter()

# Models for OpenAI-compatible API
class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str = "fabric"
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False

class ChatCompletionResponseChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class Usage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: Usage

class Model(BaseModel):
    id: str
    object: str = "model"
    created: int
    owned_by: str

class ModelsList(BaseModel):
    object: str = "list"
    data: List[Model]

# Dependency to get the Fabric integration layer
def get_fabric_integration() -> FabricIntegrationLayer:
    """Get the Fabric integration layer"""
    return FabricIntegrationLayer()

# Dependency to get the LLM
def get_llm() -> ChatOpenAI:
    """Get the language model"""
    return ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7,
        streaming=True
    )

# Dependency to get the Fabric workflow
def get_fabric_workflow(
    fabric_integration: FabricIntegrationLayer = Depends(get_fabric_integration),
    llm: ChatOpenAI = Depends(get_llm)
) -> FabricWorkflow:
    """Get the Fabric workflow"""
    return FabricWorkflow(fabric_integration, llm)

# Dependency to validate API key
async def get_api_key(api_key: str = Header(..., alias="Authorization")) -> str:
    """Validate the API key"""
    # Remove "Bearer " prefix if present
    if api_key.startswith("Bearer "):
        api_key = api_key[7:]
    
    # In a real implementation, you would validate the API key against a database
    # For now, we'll just check if it's not empty
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return api_key

@router.get("/v1/models", response_model=ModelsList)
async def list_models(
    api_key: str = Depends(get_api_key)
):
    """List available models"""
    try:
        models = [
            Model(
                id="fabric",
                created=1677610602,
                owned_by="librechat-fabric"
            )
        ]
        
        return ModelsList(data=models)
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing models"
        )

@router.post("/v1/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    api_key: str = Depends(get_api_key),
    workflow: FabricWorkflow = Depends(get_fabric_workflow)
):
    """Create a chat completion"""
    try:
        # Convert messages to Langchain format
        langchain_messages = []
        for message in request.messages:
            if message.role == "system":
                langchain_messages.append(SystemMessage(content=message.content))
            elif message.role == "user":
                langchain_messages.append(HumanMessage(content=message.content))
            elif message.role == "assistant":
                langchain_messages.append(AIMessage(content=message.content))
        
        # Invoke the workflow
        result = workflow.invoke(langchain_messages)
        
        # Extract the response
        response_messages = result["messages"]
        response_content = ""
        for message in response_messages:
            if isinstance(message, AIMessage) and message.content:
                response_content = message.content
                break
        
        # Create the response
        response = ChatCompletionResponse(
            id="chat-" + str(hash(str(request.messages))),
            created=1677610602,
            model=request.model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=Message(role="assistant", content=response_content),
                    finish_reason="stop"
                )
            ],
            usage=Usage(
                prompt_tokens=0,  # TODO: Implement token counting
                completion_tokens=0,
                total_tokens=0
            )
        )
        
        return response
    except Exception as e:
        logger.error(f"Error creating chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating chat completion"
        )

@router.post("/v1/chat/completions/stream")
async def chat_completions_stream(
    request: ChatCompletionRequest,
    api_key: str = Depends(get_api_key),
    workflow: FabricWorkflow = Depends(get_fabric_workflow)
):
    """Create a streaming chat completion"""
    try:
        # Convert messages to Langchain format
        langchain_messages = []
        for message in request.messages:
            if message.role == "system":
                langchain_messages.append(SystemMessage(content=message.content))
            elif message.role == "user":
                langchain_messages.append(HumanMessage(content=message.content))
            elif message.role == "assistant":
                langchain_messages.append(AIMessage(content=message.content))
        
        async def generate():
            try:
                # Stream the workflow
                for output in workflow.stream(langchain_messages):
                    # Extract the response
                    response_messages = output.get("messages", [])
                    response_content = ""
                    for message in response_messages:
                        if isinstance(message, AIMessage) and message.content:
                            response_content = message.content
                            break
                    
                    if response_content:
                        # Format as SSE
                        yield f"data: {response_content}\n\n"
                
                # Send the final message
                yield "data: [DONE]\n\n"
            except Exception as e:
                logger.error(f"Error in stream generation: {e}")
                yield f"data: Error: {str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )
    except Exception as e:
        logger.error(f"Error creating streaming chat completion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating streaming chat completion"
        )

@router.get("/v1/fabric/patterns")
async def get_fabric_patterns(
    api_key: str = Depends(get_api_key),
    workflow: FabricWorkflow = Depends(get_fabric_workflow)
):
    """Get available Fabric patterns"""
    try:
        patterns = workflow.get_available_patterns()
        pattern_descriptions = {
            pattern: workflow.get_pattern_description(pattern)
            for pattern in patterns
        }
        
        return {
            "patterns": patterns,
            "descriptions": pattern_descriptions
        }
    except Exception as e:
        logger.error(f"Error getting Fabric patterns: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting Fabric patterns"
        )

@router.get("/v1/fabric/tools")
async def get_fabric_tools(
    api_key: str = Depends(get_api_key),
    workflow: FabricWorkflow = Depends(get_fabric_workflow)
):
    """Get available Fabric tools"""
    try:
        tool_descriptions = workflow.get_tool_descriptions()
        
        return {
            "tools": tool_descriptions
        }
    except Exception as e:
        logger.error(f"Error getting Fabric tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error getting Fabric tools"
        )