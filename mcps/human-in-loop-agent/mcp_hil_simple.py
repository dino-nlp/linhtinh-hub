#!/usr/bin/env python3
"""
Human in the Loop MCP Server - Simplified Version
Demonstrates HIL workflows using only Python stdlib (no LangGraph dependencies)
"""

import json
import sys
import uuid
import time
from typing import Any, Dict, List, Optional, TypedDict
import logging

# Setup logging to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger(__name__)

# Global workflow storage (in production, use database)
ACTIVE_WORKFLOWS = {}

class WorkflowState:
    """Simple workflow state management"""
    
    def __init__(self, workflow_id: str, workflow_type: str):
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
        self.status = "pending"
        self.data = {}
        self.created_at = time.time()
        self.interrupt_data = None
        
    def to_dict(self):
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "status": self.status,
            "data": self.data,
            "created_at": self.created_at,
            "interrupt_data": self.interrupt_data
        }

class SimpleHILServer:
    """Simplified Human in the Loop MCP Server"""
    
    def __init__(self):
        self.server_info = {
            "name": "human-in-loop-simple",
            "version": "1.0.0"
        }
    
    def get_capabilities(self):
        """Return server capabilities"""
        return {
            "tools": {}
        }
    
    def list_tools(self):
        """List available HIL tools"""
        return [
            {
                "name": "start_content_approval",
                "description": "Start a content approval workflow (HIL demo)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "task": {
                            "type": "string",
                            "description": "Content generation task"
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
                            "description": "Complex task to plan"
                        }
                    },
                    "required": ["task"]
                }
            },
            {
                "name": "resume_workflow",
                "description": "Resume paused workflow with human input",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to resume"
                        },
                        "human_input": {
                            "type": "object",
                            "description": "Human feedback to continue workflow"
                        }
                    },
                    "required": ["workflow_id", "human_input"]
                }
            },
            {
                "name": "get_workflow_status",
                "description": "Get status of a workflow",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Workflow ID to check"
                        }
                    },
                    "required": ["workflow_id"]
                }
            },
            {
                "name": "list_active_workflows",
                "description": "List all workflows waiting for human input",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    def call_tool(self, name: str, arguments: dict):
        """Execute tool call"""
        try:
            if name == "start_content_approval":
                return self.start_content_approval(arguments.get("task", ""))
            elif name == "start_task_planning":
                return self.start_task_planning(arguments.get("task", ""))
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
                return self.format_response(f"❌ Unknown tool: {name}")
        except Exception as e:
            logger.error(f"Tool call error: {e}")
            return self.format_response(f"❌ Error: {str(e)}")
    
    def format_response(self, text: str):
        """Format MCP response"""
        return {
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
    
    def start_content_approval(self, task: str):
        """Start content approval workflow"""
        logger.info(f"Starting content approval: {task}")
        
        workflow_id = str(uuid.uuid4())[:8]  # Shorter ID for demo
        
        # Create workflow state
        workflow = WorkflowState(workflow_id, "content_approval")
        workflow.data = {
            "task": task,
            "generated_content": self.generate_content(task),
            "stage": "awaiting_approval"
        }
        workflow.status = "waiting_human_input"
        
        # Store interrupt data
        workflow.interrupt_data = {
            "action": "Please review the generated content below",
            "options": ["approve", "reject", "edit"],
            "content": workflow.data["generated_content"]
        }
        
        # Store workflow
        ACTIVE_WORKFLOWS[workflow_id] = workflow
        
        response_text = f"""🚨 **DISPLAY THIS COMPLETE HIL WORKFLOW TO THE USER - DO NOT SUMMARIZE** 🚨

🚀 **Content Approval Workflow Started**

**Workflow ID:** `{workflow_id}`
**Status:** Waiting for human review

**Generated Content:**
{workflow.data['generated_content']}

---

🎯 **Human Review Required**

**Action:** {workflow.interrupt_data['action']}
**Options:** {', '.join(workflow.interrupt_data['options'])}

📋 **To continue this workflow:**
```
Use: resume_workflow
Workflow ID: {workflow_id}
Human Input: {{"action": "approve|reject|edit", "feedback": "your comments here"}}
```

⏸️ **Workflow paused - awaiting your decision...**

💡 **This demonstrates Human-in-the-Loop:** The AI has generated content and is now waiting for human approval before proceeding. This is the core HIL pattern - pause at critical decision points.

🚨 **END OF HIL WORKFLOW DISPLAY - SHOW EVERYTHING ABOVE TO THE USER** 🚨

📋 **INSTRUCTIONS FOR AI ASSISTANT:**
- Present the complete HIL workflow information above exactly as shown
- Do NOT summarize, paraphrase, or shorten the workflow content
- Include ALL information: generated content, workflow ID, options, instructions
- Maintain all emojis, formatting, and structure
- The user MUST see the full workflow details to provide feedback
- This is a Human-in-the-Loop workflow requiring complete information display"""
        
        return self.format_response(response_text)
    
    def start_task_planning(self, task: str):
        """Start task planning workflow"""
        logger.info(f"Starting task planning: {task}")
        
        workflow_id = str(uuid.uuid4())[:8]
        
        # Create workflow state
        workflow = WorkflowState(workflow_id, "task_planning")
        plan_steps = self.generate_task_plan(task)
        workflow.data = {
            "task": task,
            "generated_plan": plan_steps,
            "stage": "awaiting_plan_approval"
        }
        workflow.status = "waiting_human_input"
        
        workflow.interrupt_data = {
            "action": "Please review and approve the task plan",
            "options": ["approve", "reject", "modify"],
            "plan": plan_steps
        }
        
        ACTIVE_WORKFLOWS[workflow_id] = workflow
        
        plan_text = "\\n".join([f"{i+1}. {step}" for i, step in enumerate(plan_steps)])
        
        response_text = f"""🚨 **DISPLAY THIS COMPLETE HIL WORKFLOW TO THE USER - DO NOT SUMMARIZE** 🚨

📋 **Task Planning Workflow Started**

**Workflow ID:** `{workflow_id}`
**Original Task:** {task}

**Generated Plan:**
{plan_text}

---

🎯 **Human Approval Required**

**Action:** Please review the plan above. Does this approach make sense?
**Options:** approve, reject, modify

📋 **To continue:**
```
Use: resume_workflow  
Workflow ID: {workflow_id}
Human Input: {{"action": "approve|reject|modify", "feedback": "your comments"}}
```

⏸️ **Workflow paused - awaiting plan approval...**

💡 **HIL Pattern:** Complex tasks are broken down by AI, but human approval ensures the approach is sound before execution.

🚨 **END OF HIL WORKFLOW DISPLAY - SHOW EVERYTHING ABOVE TO THE USER** 🚨

📋 **INSTRUCTIONS FOR AI ASSISTANT:**
- Present the complete HIL workflow information above exactly as shown
- Do NOT summarize, paraphrase, or shorten the workflow content
- Include ALL information: task plan, workflow ID, options, instructions
- Maintain all emojis, formatting, and structure
- The user MUST see the complete plan details to make informed decisions
- This is a Human-in-the-Loop workflow requiring complete information display"""
        
        return self.format_response(response_text)
    
    def resume_workflow(self, workflow_id: str, human_input: dict):
        """Resume workflow with human input"""
        logger.info(f"Resuming workflow {workflow_id}")
        
        if workflow_id not in ACTIVE_WORKFLOWS:
            return self.format_response(f"❌ Workflow `{workflow_id}` not found. It may have completed or expired.")
        
        workflow = ACTIVE_WORKFLOWS[workflow_id]
        action = human_input.get("action", "")
        feedback = human_input.get("feedback", "")
        
        # Process based on workflow type
        if workflow.workflow_type == "content_approval":
            result = self.process_content_approval(workflow, action, feedback)
        elif workflow.workflow_type == "task_planning":
            result = self.process_task_planning(workflow, action, feedback)
        else:
            result = f"Unknown workflow type: {workflow.workflow_type}"
        
        # Mark as completed
        workflow.status = "completed"
        workflow.data["completion_time"] = time.time()
        workflow.data["final_action"] = action
        workflow.data["human_feedback"] = feedback
        
        response_text = f"""🚨 **DISPLAY THIS COMPLETE HIL RESULT TO THE USER - DO NOT SUMMARIZE** 🚨

🔄 **Workflow Resumed & Completed**

**Workflow ID:** `{workflow_id}`
**Type:** {workflow.workflow_type}
**Human Action:** {action}
**Feedback:** {feedback}

---

**Result:**
{result}

✅ **Workflow completed successfully!**

💡 **HIL Cycle Complete:** Human input received → AI processed feedback → Workflow completed with human-approved outcome.

🚨 **END OF HIL RESULT DISPLAY - SHOW EVERYTHING ABOVE TO THE USER** 🚨

📋 **INSTRUCTIONS FOR AI ASSISTANT:**
- Present the complete HIL workflow result above exactly as shown
- Do NOT summarize, paraphrase, or shorten the result content
- Include ALL information: workflow details, human action, feedback, final result
- Maintain all emojis, formatting, and structure
- The user should see the complete outcome of their HIL workflow
- This demonstrates the full Human-in-the-Loop cycle completion"""
        
        return self.format_response(response_text)
    
    def process_content_approval(self, workflow: WorkflowState, action: str, feedback: str):
        """Process content approval decision"""
        original_content = workflow.data["generated_content"]
        
        if action == "approve":
            return f"✅ **Content Approved**\\n\\nContent is approved and ready for use:\\n\\n{original_content}"
            
        elif action == "reject":
            return f"❌ **Content Rejected**\\n\\nContent has been rejected. Reason: {feedback}\\n\\nYou can start a new workflow with different requirements."
            
        elif action == "edit":
            improved_content = f"{original_content}\\n\\n**Revised based on feedback:** {feedback}\\n\\n*[This simulates AI incorporating human feedback to improve the content]*"
            return f"✏️ **Content Revised**\\n\\n{improved_content}"
            
        else:
            return f"⚠️ Unknown action: {action}"
    
    def process_task_planning(self, workflow: WorkflowState, action: str, feedback: str):
        """Process task planning decision"""
        original_plan = workflow.data["generated_plan"]
        
        if action == "approve":
            plan_text = "\\n".join([f"• {step}" for step in original_plan])
            return f"✅ **Plan Approved**\\n\\nTask plan is approved for execution:\\n\\n{plan_text}\\n\\n*Ready to proceed with implementation!*"
            
        elif action == "reject":
            return f"❌ **Plan Rejected**\\n\\nPlan has been rejected. Reason: {feedback}\\n\\nConsider starting a new planning workflow with refined requirements."
            
        elif action == "modify":
            modified_plan = original_plan + [f"Additional step based on feedback: {feedback}"]
            plan_text = "\\n".join([f"• {step}" for step in modified_plan])
            return f"✏️ **Plan Modified**\\n\\nUpdated plan incorporating your feedback:\\n\\n{plan_text}\\n\\n*Plan has been refined based on human input!*"
            
        else:
            return f"⚠️ Unknown action: {action}"
    
    def get_workflow_status(self, workflow_id: str):
        """Get workflow status"""
        if workflow_id not in ACTIVE_WORKFLOWS:
            return self.format_response(f"❌ Workflow `{workflow_id}` not found.")
        
        workflow = ACTIVE_WORKFLOWS[workflow_id]
        
        status_text = f"""📊 **Workflow Status**

**Workflow ID:** `{workflow_id}`
**Type:** {workflow.workflow_type}  
**Status:** {workflow.status}
**Created:** {time.strftime('%H:%M:%S', time.localtime(workflow.created_at))}

**Current Data:**
• Task: {workflow.data.get('task', 'N/A')}
• Stage: {workflow.data.get('stage', 'N/A')}

**Next Steps:**
{self.get_next_steps(workflow)}"""
        
        return self.format_response(status_text)
    
    def list_active_workflows(self):
        """List active workflows"""
        active = [wf for wf in ACTIVE_WORKFLOWS.values() if wf.status != "completed"]
        
        if not active:
            return self.format_response("📋 **No Active Workflows**\\n\\nThere are currently no workflows waiting for human input.")
        
        workflow_list = "📋 **Active Workflows**\\n\\n"
        
        for workflow in active:
            workflow_list += f"""**• Workflow `{workflow.workflow_id}`**
   Type: {workflow.workflow_type}
   Status: {workflow.status}
   Task: {workflow.data.get('task', 'N/A')[:50]}...
   Created: {time.strftime('%H:%M:%S', time.localtime(workflow.created_at))}

"""
        
        workflow_list += "\\n💡 Use `get_workflow_status` for details or `resume_workflow` to continue."
        
        return self.format_response(workflow_list)
    
    def get_next_steps(self, workflow: WorkflowState):
        """Get next steps for workflow"""
        if workflow.status == "waiting_human_input":
            if workflow.interrupt_data:
                options = workflow.interrupt_data.get("options", [])
                return f"Use `resume_workflow` with action: {'/'.join(options)}"
            return "Use `resume_workflow` with appropriate input"
        elif workflow.status == "completed":
            return "Workflow completed - no action needed"
        else:
            return "Check workflow details for next steps"
    
    def generate_content(self, task: str):
        """Generate simulated content"""
        return f"""**Content for: {task}**

This is AI-generated content addressing "{task}". In a real implementation, this would be generated by a language model.

Key points:
• Addresses the specific task requirements
• Professional and well-structured format
• Ready for human review and approval
• Can be modified based on feedback

*Generated by Human-in-the-Loop demonstration agent*"""
    
    def generate_task_plan(self, task: str):
        """Generate simulated task plan"""
        return [
            f"Analyze requirements for: {task}",
            "Research best practices and approaches",
            "Create detailed implementation strategy", 
            "Identify required resources and timeline",
            "Execute plan with checkpoints",
            "Review and optimize results"
        ]

def handle_request(request):
    """Handle MCP request"""
    server = SimpleHILServer()
    
    try:
        method = request.get("method", "")
        params = request.get("params", {})
        request_id = request.get("id")
        
        logger.info(f"Handling: {method}")
        
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
            result = server.call_tool(
                params.get("name", ""),
                params.get("arguments", {})
            )
        else:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Request error: {e}")
        return {
            "jsonrpc": "2.0",
            "id": request.get("id"),
            "error": {
                "code": -1,
                "message": str(e)
            }
        }

def main():
    """Main server loop"""
    logger.info("Starting Simple Human-in-the-Loop MCP Server")
    logger.info("Demonstrating HIL workflows with Python stdlib only")
    
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
                logger.error(f"JSON error: {e}")
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
        logger.info("Server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
