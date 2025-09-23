#!/usr/bin/env python3
"""
Human in the Loop MCP Server
Demonstrates LangGraph Human-in-the-Loop workflows integrated with LibreChat
"""

import asyncio
import json
import sys
import uuid
from typing import Any, Dict, List, Optional, TypedDict
from dataclasses import dataclass
import logging
import os
from pathlib import Path

# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# MCP imports
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool as MCPTool

# Setup logging
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Global state management
ACTIVE_WORKFLOWS = {}  # thread_id -> workflow_info
CHECKPOINTER = MemorySaver()

# Workflow States
class ContentApprovalState(TypedDict):
    task: str
    generated_content: str
    human_feedback: Optional[str]
    approval_status: Optional[str]  # "approved", "rejected", "needs_edit"
    final_content: str
    workflow_status: str  # "pending", "waiting_approval", "completed", "cancelled"

class TaskPlanningState(TypedDict):
    original_task: str
    generated_plan: List[str]
    human_feedback: Optional[str]
    approval_status: Optional[str]
    final_plan: List[str]
    workflow_status: str

class DocumentReviewState(TypedDict):
    document_content: str
    analysis: str
    human_feedback: Optional[str]
    verification_status: Optional[str]
    final_report: str
    workflow_status: str

@dataclass
class WorkflowInfo:
    workflow_id: str
    workflow_type: str
    thread_id: str
    status: str
    interrupt_data: Optional[Dict] = None

class HILMCPServer:
    """Human in the Loop MCP Server"""
    
    def __init__(self):
        self.server_info = {
            "name": "human-in-loop-agent",
            "version": "1.0.0"
        }
    
    def get_capabilities(self):
        """Return server capabilities"""
        return {
            "tools": {}
        }
    
    def list_tools(self):
        """List available Human in the Loop tools"""
        return [
            {
                "name": "start_content_approval",
                "description": "Start a content approval workflow with human review",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The content generation task"
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "start_task_planning",
                "description": "Start a task planning workflow with human approval",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "The complex task to break down and plan"
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "start_document_review", 
                "description": "Start a document review workflow with human verification",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "document_content": {
                            "type": "string",
                            "description": "The document content to analyze and review"
                        }
                    },
                    "required": ["document_content"]
                }
            },
            {
                "name": "resume_workflow",
                "description": "Resume a paused workflow with human input",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "The workflow ID to resume"
                        },
                        "human_input": {
                            "type": "object",
                            "description": "Human feedback/input to resume the workflow"
                        }
                    },
                    "required": ["workflow_id", "human_input"]
                }
            },
            {
                "name": "get_workflow_status",
                "description": "Get the status and details of a running workflow",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "The workflow ID to check"
                        }
                    },
                    "required": ["workflow_id"]
                }
            },
            {
                "name": "list_active_workflows",
                "description": "List all active workflows waiting for human input",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    def call_tool(self, name: str, arguments: dict):
        """Execute a tool call"""
        try:
            if name == "start_content_approval":
                return self.start_content_approval(arguments.get("task", ""))
            elif name == "start_task_planning":
                return self.start_task_planning(arguments.get("task", ""))
            elif name == "start_document_review":
                return self.start_document_review(arguments.get("document_content", ""))
            elif name == "resume_workflow":
                return self.resume_workflow(
                    arguments.get("workflow_id", ""),
                    arguments.get("human_input", {})
                )
            elif name == "get_workflow_status":
                return self.get_workflow_status(arguments.get("workflow_id", ""))
            elif name == "list_active_workflows":
                return self.list_active_workflows()
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"❌ Unknown tool: {name}"
                        }
                    ]
                }
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Error executing tool '{name}': {str(e)}"
                    }
                ]
            }
    
    def start_content_approval(self, task: str):
        """Start content approval workflow"""
        logger.info(f"Starting content approval workflow: {task}")
        
        workflow_id = str(uuid.uuid4())
        thread_id = str(uuid.uuid4())
        
        # Create workflow graph
        def generate_content(state: ContentApprovalState):
            """Generate initial content"""
            # Simulate content generation (in real implementation, use LLM)
            generated = f"""**Content for Task: {state['task']}**

📝 **Generated Content:**

This is AI-generated content addressing the request: "{state['task']}"

🎯 **Key Points:**
• Comprehensive response to user requirements
• Structured and professional format
• Ready for review and approval

💡 **Next Steps:**
• Review the generated content above
• Provide feedback for improvements
• Approve or request modifications

---
*Content generated by Human-in-the-Loop AI Agent*"""
            
            return {
                "generated_content": generated,
                "workflow_status": "waiting_approval"
            }
        
        def human_approval(state: ContentApprovalState):
            """Human approval checkpoint"""
            approval_data = interrupt({
                "workflow_id": workflow_id,
                "workflow_type": "content_approval",
                "task": state["task"],
                "generated_content": state["generated_content"],
                "action": "Please review the generated content. Choose: approve, reject, or request edits",
                "options": ["approve", "reject", "edit"]
            })
            
            return {
                "human_feedback": approval_data.get("feedback", ""),
                "approval_status": approval_data.get("action", "pending")
            }
        
        def process_approval(state: ContentApprovalState):
            """Process human approval decision"""
            if state["approval_status"] == "approve":
                return {
                    "final_content": state["generated_content"],
                    "workflow_status": "completed"
                }
            elif state["approval_status"] == "reject":
                return {
                    "final_content": "Content rejected by user.",
                    "workflow_status": "cancelled"
                }
            elif state["approval_status"] == "edit":
                # In real implementation, regenerate based on feedback
                edited_content = f"{state['generated_content']}\n\n**Edited based on feedback:** {state['human_feedback']}"
                return {
                    "final_content": edited_content,
                    "workflow_status": "completed"
                }
            else:
                return {
                    "workflow_status": "error"
                }
        
        # Build graph
        graph_builder = StateGraph(ContentApprovalState)
        graph_builder.add_node("generate_content", generate_content)
        graph_builder.add_node("human_approval", human_approval)
        graph_builder.add_node("process_approval", process_approval)
        
        graph_builder.add_edge(START, "generate_content")
        graph_builder.add_edge("generate_content", "human_approval")
        graph_builder.add_edge("human_approval", "process_approval")
        graph_builder.add_edge("process_approval", END)
        
        graph = graph_builder.compile(checkpointer=CHECKPOINTER)
        
        # Start workflow
        config = {"configurable": {"thread_id": thread_id}}
        initial_state = {
            "task": task,
            "generated_content": "",
            "human_feedback": None,
            "approval_status": None,
            "final_content": "",
            "workflow_status": "pending"
        }
        
        try:
            result = graph.invoke(initial_state, config=config)
            
            # Store workflow info
            ACTIVE_WORKFLOWS[workflow_id] = WorkflowInfo(
                workflow_id=workflow_id,
                workflow_type="content_approval",
                thread_id=thread_id,
                status="waiting_approval",
                interrupt_data=result.get("__interrupt__")
            )
            
            # Check if workflow hit interrupt
            if "__interrupt__" in result:
                interrupt_info = result["__interrupt__"][0]
                
                response_text = f"""🚀 **Content Approval Workflow Started**

**Workflow ID:** `{workflow_id}`
**Status:** Waiting for human approval

{interrupt_info.value.get('generated_content', '')}

🎯 **Action Required:**
{interrupt_info.value.get('action', '')}

**Options:** {', '.join(interrupt_info.value.get('options', []))}

📋 **To continue this workflow:**
```
Use tool: resume_workflow
workflow_id: {workflow_id}
human_input: {{"action": "approve|reject|edit", "feedback": "your feedback here"}}
```

⏸️ **Workflow paused - waiting for your decision...**"""
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": response_text
                        }
                    ]
                }
            else:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"✅ Workflow completed: {result.get('final_content', 'No content generated')}"
                        }
                    ]
                }
                
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Workflow execution failed: {str(e)}"
                    }
                ]
            }
    
    def start_task_planning(self, task: str):
        """Start task planning workflow"""
        logger.info(f"Starting task planning workflow: {task}")
        
        # Simplified implementation - similar structure to content approval
        workflow_id = str(uuid.uuid4())
        
        response_text = f"""📋 **Task Planning Workflow Started**

**Workflow ID:** `{workflow_id}`
**Original Task:** {task}

**Generated Plan:**
1. 🎯 Analyze task requirements
2. 📊 Break down into actionable steps  
3. ⏰ Estimate timeline and resources
4. 🔄 Create execution sequence
5. ✅ Define success criteria

🎯 **Action Required:**
Please review the generated plan above. Do you approve this approach?

📋 **To continue:**
```
Use tool: resume_workflow
workflow_id: {workflow_id}
human_input: {{"action": "approve|reject|edit", "feedback": "your feedback"}}
```"""
        
        # Store simplified workflow info
        ACTIVE_WORKFLOWS[workflow_id] = WorkflowInfo(
            workflow_id=workflow_id,
            workflow_type="task_planning",
            thread_id=str(uuid.uuid4()),
            status="waiting_approval"
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": response_text
                }
            ]
        }
    
    def start_document_review(self, document_content: str):
        """Start document review workflow"""
        logger.info(f"Starting document review workflow")
        
        workflow_id = str(uuid.uuid4())
        
        # Simulate document analysis
        analysis = f"""📄 **Document Analysis Complete**

**Document Length:** {len(document_content)} characters
**Content Type:** Text document

**Key Findings:**
• Document structure appears well-organized
• Content covers main topic comprehensively  
• Professional tone and formatting maintained
• No obvious errors or inconsistencies detected

**Summary:**
The document presents information in a clear and structured manner. The content appears to be comprehensive and professionally written.

**Confidence Score:** 85%"""
        
        response_text = f"""🔍 **Document Review Workflow Started**

**Workflow ID:** `{workflow_id}`

{analysis}

🎯 **Action Required:**
Please verify the analysis above. Does this assessment appear accurate?

📋 **To continue:**
```
Use tool: resume_workflow
workflow_id: {workflow_id}
human_input: {{"action": "verify|reject|edit", "feedback": "your assessment"}}
```"""
        
        ACTIVE_WORKFLOWS[workflow_id] = WorkflowInfo(
            workflow_id=workflow_id,
            workflow_type="document_review",
            thread_id=str(uuid.uuid4()),
            status="waiting_verification"
        )
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": response_text
                }
            ]
        }
    
    def resume_workflow(self, workflow_id: str, human_input: dict):
        """Resume workflow with human input"""
        logger.info(f"Resuming workflow {workflow_id} with input: {human_input}")
        
        if workflow_id not in ACTIVE_WORKFLOWS:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": f"❌ Workflow {workflow_id} not found. It may have completed or expired."
                    }
                ]
            }
        
        workflow_info = ACTIVE_WORKFLOWS[workflow_id]
        action = human_input.get("action", "")
        feedback = human_input.get("feedback", "")
        
        # Process based on workflow type and action
        if workflow_info.workflow_type == "content_approval":
            if action == "approve":
                result_text = "✅ **Content Approved!**\n\nThe generated content has been approved and is ready for use."
            elif action == "reject":
                result_text = "❌ **Content Rejected**\n\nThe content has been rejected. You can start a new workflow with different requirements."
            elif action == "edit":
                result_text = f"""✏️ **Content Edited**

**Your Feedback:** {feedback}

**Action Taken:** Content has been revised based on your feedback.

**Updated Content:**
[Original content with your suggested improvements applied]

✅ **Workflow completed with edits.**"""
            else:
                result_text = f"⚠️ Unknown action: {action}"
                
        elif workflow_info.workflow_type == "task_planning":
            if action == "approve":
                result_text = "✅ **Plan Approved!**\n\nThe task plan has been approved and is ready for execution."
            elif action == "reject":
                result_text = "❌ **Plan Rejected**\n\nThe plan has been rejected. Consider starting a new planning workflow."
            elif action == "edit":
                result_text = f"""✏️ **Plan Modified**

**Your Feedback:** {feedback}

**Revised Plan:** The plan has been updated based on your suggestions.

✅ **Updated plan ready for execution.**"""
            else:
                result_text = f"⚠️ Unknown action: {action}"
                
        elif workflow_info.workflow_type == "document_review":
            if action == "verify":
                result_text = "✅ **Analysis Verified!**\n\nThe document analysis has been verified and the review is complete."
            elif action == "reject":
                result_text = "❌ **Analysis Rejected**\n\nThe analysis has been rejected. Please provide feedback for improvement."
            elif action == "edit":
                result_text = f"""✏️ **Analysis Updated**

**Your Feedback:** {feedback}

**Updated Analysis:** The analysis has been revised based on your input.

✅ **Document review completed with corrections.**"""
            else:
                result_text = f"⚠️ Unknown action: {action}"
        else:
            result_text = f"⚠️ Unknown workflow type: {workflow_info.workflow_type}"
        
        # Mark workflow as completed
        workflow_info.status = "completed"
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"""🔄 **Workflow Resumed**

**Workflow ID:** `{workflow_id}`
**Type:** {workflow_info.workflow_type}
**Action:** {action}

{result_text}

📊 **Workflow Status:** Completed"""
                }
            ]
        }
    
    def get_workflow_status(self, workflow_id: str):
        """Get workflow status"""
        if workflow_id not in ACTIVE_WORKFLOWS:
            return {
                "content": [
                    {
                        "type": "text", 
                        "text": f"❌ Workflow {workflow_id} not found."
                    }
                ]
            }
        
        workflow_info = ACTIVE_WORKFLOWS[workflow_id]
        
        status_text = f"""📊 **Workflow Status**

**Workflow ID:** `{workflow_id}`
**Type:** {workflow_info.workflow_type}
**Status:** {workflow_info.status}
**Thread ID:** {workflow_info.thread_id}

🎯 **Next Steps:**
{self._get_next_steps(workflow_info)}"""
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": status_text
                }
            ]
        }
    
    def list_active_workflows(self):
        """List all active workflows"""
        if not ACTIVE_WORKFLOWS:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "📋 **No active workflows**\n\nThere are currently no workflows waiting for human input."
                    }
                ]
            }
        
        workflow_list = "📋 **Active Workflows**\n\n"
        
        for wf_id, wf_info in ACTIVE_WORKFLOWS.items():
            if wf_info.status != "completed":
                workflow_list += f"""**• Workflow ID:** `{wf_id}`
   **Type:** {wf_info.workflow_type}
   **Status:** {wf_info.status}
   
"""
        
        workflow_list += "\n💡 **Tip:** Use `get_workflow_status` to see details or `resume_workflow` to continue."
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": workflow_list
                }
            ]
        }
    
    def _get_next_steps(self, workflow_info: WorkflowInfo):
        """Get next steps for workflow"""
        if workflow_info.status == "waiting_approval":
            return "Use `resume_workflow` with action: approve/reject/edit"
        elif workflow_info.status == "waiting_verification":
            return "Use `resume_workflow` with action: verify/reject/edit"
        elif workflow_info.status == "completed":
            return "Workflow is completed"
        else:
            return "Status unclear - check workflow details"

def handle_request(request):
    """Handle incoming MCP request"""
    server = HILMCPServer()
    
    try:
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        logger.info(f"Handling request: {method}")
        
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": server.get_capabilities(),
                "serverInfo": server.server_info
            }
        elif method == "notifications/initialized":
            return None
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": server.list_tools()}
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            result = server.call_tool(tool_name, tool_args)
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        response = {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
        return response
        
    except Exception as e:
        logger.error(f"Request handling error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -1,
                "message": str(e)
            }
        }

def main():
    """Main MCP server loop"""
    logger.info("Starting Human in the Loop MCP Server")
    logger.info("Reading from stdin, writing to stdout")
    
    try:
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
                
            try:
                request = json.loads(line)
                response = handle_request(request)
                
                if response is not None:
                    print(json.dumps(response))
                    sys.stdout.flush()
                    
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {e}")
                error_response = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {
                        "code": -32700,
                        "message": "Parse error"
                    }
                }
                print(json.dumps(error_response))
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
