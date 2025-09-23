#!/usr/bin/env python3
"""
Research AI Agent MCP Server (SSE Transport)
A LangGraph-powered multi-agent system for comprehensive research tasks
Supports both SSE and stdio transports for Docker compatibility
"""

import asyncio
import json
import sys
import os
from typing import Any, Dict, List, Optional, Sequence
from dataclasses import dataclass

import httpx
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import Tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.memory import MemorySaver
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.sse import SseServerTransport
from mcp.types import TextContent, Tool as MCPTool, CallToolRequest
import logging
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response
import uvicorn

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class ResearchState(MessagesState):
    """Extended state for research workflow"""
    research_data: Optional[Dict[str, Any]] = None
    analysis_results: Optional[Dict[str, Any]] = None
    current_step: str = "initial"


class ResearchAgent:
    """Research specialist agent"""
    
    def __init__(self, llm):
        self.llm = llm
        self.search_tool = DuckDuckGoSearchRun()
        
    def search_and_gather(self, query: str) -> str:
        """Search for information and gather relevant data"""
        try:
            search_results = self.search_tool.invoke(query)
            
            # Use LLM to summarize and extract key information
            prompt = f"""
            Based on the following search results for query: "{query}"
            
            Search Results:
            {search_results}
            
            Please provide a well-structured summary that includes:
            1. Key findings and facts
            2. Important statistics or data points
            3. Recent developments or trends
            4. Credible sources mentioned
            
            Format the response in a clear, organized manner.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Error in search_and_gather: {e}")
            return f"Error searching for information: {str(e)}"


class AnalysisAgent:
    """Analysis specialist agent"""
    
    def __init__(self, llm):
        self.llm = llm
        
    def analyze_data(self, research_data: str, analysis_focus: str) -> str:
        """Analyze research data with specific focus"""
        try:
            prompt = f"""
            You are an expert analyst. Analyze the following research data with focus on: {analysis_focus}
            
            Research Data:
            {research_data}
            
            Please provide:
            1. Key patterns and trends identified
            2. Critical insights and implications
            3. Strengths and limitations of the data
            4. Recommendations based on analysis
            5. Areas requiring further investigation
            
            Structure your analysis clearly with headings and bullet points.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Error in analyze_data: {e}")
            return f"Error analyzing data: {str(e)}"


class SynthesisAgent:
    """Synthesis and reporting agent"""
    
    def __init__(self, llm):
        self.llm = llm
        
    def create_report(self, research_data: str, analysis_results: str, report_type: str = "comprehensive") -> str:
        """Create final synthesized report"""
        try:
            prompt = f"""
            You are an expert report writer. Create a {report_type} report based on the research and analysis below.
            
            Research Data:
            {research_data}
            
            Analysis Results:
            {analysis_results}
            
            Create a professional report that includes:
            1. Executive Summary
            2. Key Findings
            3. Detailed Analysis
            4. Conclusions and Recommendations
            5. Future Outlook
            
            Use clear headings, bullet points, and professional formatting.
            Make it comprehensive but concise.
            """
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            return response.content
            
        except Exception as e:
            logger.error(f"Error in create_report: {e}")
            return f"Error creating report: {str(e)}"


class ResearchWorkflow:
    """LangGraph workflow for multi-agent research"""
    
    def __init__(self, model_provider: str = "openai", model_name: str = "gpt-4"):
        # Initialize LLM
        if model_provider.lower() == "openai":
            self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        elif model_provider.lower() == "anthropic":
            self.llm = ChatAnthropic(model=model_name, temperature=0.1)
        else:
            raise ValueError(f"Unsupported model provider: {model_provider}")
            
        # Initialize agents
        self.research_agent = ResearchAgent(self.llm)
        self.analysis_agent = AnalysisAgent(self.llm)
        self.synthesis_agent = SynthesisAgent(self.llm)
        
        # Build workflow
        self.workflow = self._build_workflow()
        
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        def supervisor_node(state: ResearchState) -> ResearchState:
            """Supervisor node to control workflow"""
            messages = state.messages
            current_step = state.current_step
            
            if current_step == "initial":
                return ResearchState(
                    messages=messages,
                    current_step="research",
                    research_data=state.research_data,
                    analysis_results=state.analysis_results
                )
            elif current_step == "research" and state.research_data:
                return ResearchState(
                    messages=messages,
                    current_step="analysis",
                    research_data=state.research_data,
                    analysis_results=state.analysis_results
                )
            elif current_step == "analysis" and state.analysis_results:
                return ResearchState(
                    messages=messages,
                    current_step="synthesis",
                    research_data=state.research_data,
                    analysis_results=state.analysis_results
                )
            else:
                return ResearchState(
                    messages=messages,
                    current_step="complete",
                    research_data=state.research_data,
                    analysis_results=state.analysis_results
                )
        
        def research_node(state: ResearchState) -> ResearchState:
            """Research agent node"""
            query = state.messages[-1].content if state.messages else ""
            research_data = self.research_agent.search_and_gather(query)
            
            new_message = AIMessage(content=f"Research completed: {research_data[:200]}...")
            
            return ResearchState(
                messages=state.messages + [new_message],
                current_step="research_complete",
                research_data=research_data,
                analysis_results=state.analysis_results
            )
        
        def analysis_node(state: ResearchState) -> ResearchState:
            """Analysis agent node"""
            if not state.research_data:
                return state
                
            analysis_focus = "trends, patterns, and key insights"
            analysis_results = self.analysis_agent.analyze_data(state.research_data, analysis_focus)
            
            new_message = AIMessage(content=f"Analysis completed: {analysis_results[:200]}...")
            
            return ResearchState(
                messages=state.messages + [new_message],
                current_step="analysis_complete",
                research_data=state.research_data,
                analysis_results=analysis_results
            )
        
        def synthesis_node(state: ResearchState) -> ResearchState:
            """Synthesis agent node"""
            if not state.research_data or not state.analysis_results:
                return state
                
            final_report = self.synthesis_agent.create_report(
                state.research_data, 
                state.analysis_results,
                "comprehensive"
            )
            
            new_message = AIMessage(content=final_report)
            
            return ResearchState(
                messages=state.messages + [new_message],
                current_step="complete",
                research_data=state.research_data,
                analysis_results=state.analysis_results
            )
        
        def should_continue(state: ResearchState) -> str:
            """Determine next step in workflow"""
            if state.current_step == "research":
                return "research_node"
            elif state.current_step == "analysis":
                return "analysis_node"
            elif state.current_step == "synthesis":
                return "synthesis_node"
            else:
                return END
        
        # Build graph
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("research_node", research_node)
        workflow.add_node("analysis_node", analysis_node)
        workflow.add_node("synthesis_node", synthesis_node)
        
        # Add edges
        workflow.add_edge(START, "supervisor")
        workflow.add_conditional_edges(
            "supervisor",
            should_continue,
            {
                "research_node": "research_node",
                "analysis_node": "analysis_node", 
                "synthesis_node": "synthesis_node",
                END: END
            }
        )
        workflow.add_edge("research_node", "supervisor")
        workflow.add_edge("analysis_node", "supervisor")
        workflow.add_edge("synthesis_node", END)
        
        # Compile with memory
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)
    
    async def run_research(self, query: str, workflow_type: str = "full") -> Dict[str, Any]:
        """Run the research workflow"""
        try:
            config = {"configurable": {"thread_id": "research_session"}}
            
            initial_state = ResearchState(
                messages=[HumanMessage(content=query)],
                current_step="initial"
            )
            
            # Run workflow
            result = await self.workflow.ainvoke(initial_state, config)
            
            return {
                "success": True,
                "query": query,
                "workflow_type": workflow_type,
                "final_report": result.messages[-1].content if result.messages else "",
                "research_data": result.research_data,
                "analysis_results": result.analysis_results,
                "steps_completed": len(result.messages),
                "status": "completed"
            }
            
        except Exception as e:
            logger.error(f"Error in run_research: {e}")
            return {
                "success": False,
                "error": str(e),
                "query": query,
                "status": "failed"
            }


class MCPResearchServer:
    """MCP Server for Research AI Agent"""
    
    def __init__(self):
        self.research_workflow = None
        
    def initialize_workflow(self, model_provider: str = "openai", model_name: str = "gpt-4"):
        """Initialize the research workflow"""
        try:
            self.research_workflow = ResearchWorkflow(model_provider, model_name)
            logger.info(f"Research workflow initialized with {model_provider} {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize workflow: {e}")
            raise
    
    def get_tools(self) -> List[MCPTool]:
        """Get available MCP tools"""
        return [
            MCPTool(
                name="research_comprehensive",
                description="Conduct comprehensive research using multi-agent system with search, analysis, and synthesis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Research topic or question to investigate"
                        },
                        "focus_area": {
                            "type": "string", 
                            "description": "Specific area to focus analysis on (optional)",
                            "default": "general insights and trends"
                        },
                        "report_type": {
                            "type": "string",
                            "enum": ["quick", "comprehensive", "detailed"],
                            "description": "Type of report to generate",
                            "default": "comprehensive"
                        }
                    },
                    "required": ["query"]
                }
            ),
            MCPTool(
                name="research_quick",
                description="Quick research and summary on a topic",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Research topic or question"
                        }
                    },
                    "required": ["query"]
                }
            )
        ]
    
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> List[TextContent]:
        """Handle tool calls"""
        if not self.research_workflow:
            return [TextContent(
                type="text",
                text=json.dumps({
                    "error": "Research workflow not initialized. Please check configuration."
                })
            )]
        
        try:
            if name == "research_comprehensive":
                result = await self.research_workflow.run_research(
                    query=arguments["query"],
                    workflow_type="comprehensive"
                )
            elif name == "research_quick":
                # For quick research, just use research agent
                research_agent = ResearchAgent(self.research_workflow.llm)
                research_data = research_agent.search_and_gather(arguments["query"])
                result = {
                    "success": True,
                    "query": arguments["query"],
                    "workflow_type": "quick",
                    "final_report": research_data,
                    "status": "completed"
                }
            else:
                result = {
                    "success": False,
                    "error": f"Unknown tool: {name}"
                }
            
            return [TextContent(type="text", text=json.dumps(result, indent=2))]
            
        except Exception as e:
            logger.error(f"Error calling tool {name}: {e}")
            return [TextContent(
                type="text", 
                text=json.dumps({
                    "success": False,
                    "error": str(e),
                    "tool": name
                })
            )]


async def run_sse_server(host: str = "0.0.0.0", port: int = 8000):
    """Run MCP server with SSE transport"""
    # Initialize MCP server
    mcp_server = MCPResearchServer()
    
    # Try to initialize workflow
    try:
        mcp_server.initialize_workflow()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        sys.exit(1)
    
    # Create MCP server
    server = Server("research-ai-agent")
    
    @server.list_tools()
    async def handle_list_tools() -> List[MCPTool]:
        return mcp_server.get_tools()
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
        return await mcp_server.call_tool(name, arguments)
    
    # Create FastAPI app
    app = FastAPI(
        title="Research AI Agent MCP Server",
        description="LangGraph-powered multi-agent research system",
        version="1.0.0"
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {
            "status": "healthy",
            "server": "research-ai-agent",
            "version": "1.0.0",
            "tools_count": len(mcp_server.get_tools())
        }
    
    # MCP SSE endpoint - support GET, POST, and HEAD methods
    @app.get("/sse")
    @app.post("/sse") 
    @app.head("/sse")
    async def handle_sse(request: Request):
        """Handle MCP over SSE"""
        logger.info(f"SSE request received: {request.method} {request.url}")
        
        try:
            # Handle HEAD requests (just return headers)
            if request.method == "HEAD":
                return Response(
                    status_code=200,
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive", 
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
                        "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization",
                        "Content-Type": "text/event-stream"
                    }
                )
            
            # Proper MCP protocol implementation
            async def generate():
                # Send MCP initialization
                init_response = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "tools": {
                                "listChanged": True
                            }
                        },
                        "serverInfo": {
                            "name": "research-ai-agent",
                            "version": "1.0.0"
                        }
                    }
                }
                yield f"data: {json.dumps(init_response)}\n\n"
                
                # Send tools list
                tools_list = {
                    "jsonrpc": "2.0", 
                    "id": 2,
                    "result": {
                        "tools": [
                            {
                                "name": "research_comprehensive",
                                "description": "Execute a multi-agent workflow using specialized AI agents for research, analysis, and reporting",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "task": {
                                            "type": "string",
                                            "description": "The task to be executed by the multi-agent system"
                                        },
                                        "workflow_type": {
                                            "type": "string",
                                            "enum": ["research", "analysis", "full_pipeline"],
                                            "description": "Type of workflow to execute"
                                        }
                                    },
                                    "required": ["task"]
                                }
                            },
                            {
                                "name": "research_quick",
                                "description": "Quick research and summary on a topic",
                                "inputSchema": {
                                    "type": "object",
                                    "properties": {
                                        "query": {
                                            "type": "string",
                                            "description": "Research topic or question"
                                        }
                                    },
                                    "required": ["query"]
                                }
                            }
                        ]
                    }
                }
                yield f"data: {json.dumps(tools_list)}\n\n"
                
                # Handle the request body if it exists
                if request.method == "POST":
                    try:
                        body = await request.body()
                        if body:
                            logger.info(f"Received POST data: {body.decode()}")
                            # Parse and handle MCP requests here
                    except Exception as e:
                        logger.error(f"Error reading request body: {e}")
                
                # Keep connection alive with proper MCP pings
                while True:
                    ping = {
                        "jsonrpc": "2.0",
                        "method": "notifications/ping"
                    }
                    yield f"data: {json.dumps(ping)}\n\n"
                    await asyncio.sleep(30)  # Send ping every 30 seconds
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, HEAD, OPTIONS",
                    "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization"
                }
            )
            
        except Exception as e:
            logger.error(f"SSE error: {e}")
            return {"error": str(e)}
    
    # CORS options handler
    @app.options("/sse")
    async def handle_options():
        return {
            "status": "ok",
            "headers": {
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Accept, Authorization"
            }
        }
    
    # Start server
    logger.info(f"Starting Research AI Agent MCP Server on {host}:{port}")
    logger.info(f"Health check: http://{host}:{port}/health")
    logger.info(f"MCP SSE endpoint: http://{host}:{port}/sse")
    
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


async def run_stdio_server():
    """Run MCP server with stdio transport (for backward compatibility)"""
    # Initialize MCP server
    mcp_server = MCPResearchServer()
    
    # Try to initialize workflow
    try:
        mcp_server.initialize_workflow()
    except Exception as e:
        logger.error(f"Failed to initialize: {e}")
        sys.exit(1)
    
    # Create MCP server
    server = Server("research-ai-agent")
    
    @server.list_tools()
    async def handle_list_tools() -> List[MCPTool]:
        return mcp_server.get_tools()
    
    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict) -> List[TextContent]:
        return await mcp_server.call_tool(name, arguments)
    
    # Run server
    logger.info("Starting Research AI Agent MCP Server (stdio mode)...")
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """Main function with transport selection"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Research AI Agent MCP Server")
    parser.add_argument(
        "--transport", 
        choices=["sse", "stdio"], 
        default="sse",
        help="Transport type (default: sse)"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0",
        help="Host to bind SSE server (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", 
        type=int,
        default=8000,
        help="Port for SSE server (default: 8000)"
    )
    
    args = parser.parse_args()
    
    if args.transport == "sse":
        asyncio.run(run_sse_server(args.host, args.port))
    else:
        asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
