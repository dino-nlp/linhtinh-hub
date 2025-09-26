import logging
from typing import Dict, Any, Optional, List, TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import END, Graph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolExecutor, ToolInvocation
from ..core.fabric_integration import FabricIntegrationLayer
from ..tools.fabric_tools import FabricTools

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """The state of the agent"""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    is_last_step: bool

class FabricWorkflow:
    """Langgraph workflow for Fabric pattern execution"""
    
    def __init__(self, fabric_integration: FabricIntegrationLayer, llm):
        """
        Initialize the Fabric workflow
        
        Args:
            fabric_integration: The Fabric integration layer
            llm: The language model to use for the workflow
        """
        self.fabric_integration = fabric_integration
        self.fabric_tools = FabricTools(fabric_integration)
        self.llm = llm
        self.tool_executor = ToolExecutor(self.fabric_tools.tools)
        self.workflow = self._create_workflow()
    
    def _create_workflow(self) -> Graph:
        """Create the Langgraph workflow"""
        workflow = Graph()
        
        # Add nodes
        workflow.add_node("agent", self._agent_node)
        workflow.add_node("tools", self._tool_node)
        
        # Set entry point
        workflow.add_edge(START, "agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": END
            }
        )
        
        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")
        
        return workflow.compile()
    
    def _agent_node(self, state: AgentState) -> AgentState:
        """Process the agent node"""
        messages = state["messages"]
        
        # Create a system message that instructs the agent on how to use the tools
        system_message = SystemMessage(
            content=(
                "You are a helpful assistant that can use Fabric tools to process text. "
                "You have access to the following tools:\n"
                "- summarize: Summarize the input text\n"
                "- analyze_claims: Analyze claims in the input text\n"
                "- extract_wisdom: Extract wisdom from the input text\n"
                "- improve_writing: Improve the writing in the input text\n"
                "- translate: Translate the input text to a target language\n\n"
                "When using a tool, make sure to provide all required parameters. "
                "After receiving the tool output, provide a helpful response to the user "
                "that incorporates the tool results."
            )
        )
        
        # Create the prompt template
        prompt = ChatPromptTemplate.from_messages([
            system_message,
            MessagesPlaceholder(variable_name="messages"),
        ])
        
        # Bind tools to the LLM
        llm_with_tools = self.llm.bind_tools(self.fabric_tools.tools)
        
        # Create the chain
        chain = prompt | llm_with_tools
        
        # Invoke the chain
        response = chain.invoke({"messages": messages})
        
        # Return the updated state
        return {"messages": [response], "is_last_step": False}
    
    def _tool_node(self, state: AgentState) -> AgentState:
        """Process the tool node"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # Execute the tools
        tool_invocations = []
        
        for tool_call in last_message.tool_calls:
            tool_invocation = ToolInvocation(
                tool=tool_call["name"],
                tool_input=tool_call["args"]
            )
            tool_invocations.append(tool_invocation)
        
        # Execute the tools
        tool_outputs = self.tool_executor.batch(tool_invocations)
        
        # Create tool messages
        tool_messages = []
        for tool_output, tool_call in zip(tool_outputs, last_message.tool_calls):
            tool_message = {
                "role": "tool",
                "content": tool_output,
                "tool_call_id": tool_call["id"]
            }
            tool_messages.append(tool_message)
        
        # Return the updated state
        return {"messages": tool_messages, "is_last_step": False}
    
    def _should_continue(self, state: AgentState) -> str:
        """Determine if we should continue to tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has tool calls, continue to tools
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            return "continue"
        
        # Otherwise, end
        return "end"
    
    def invoke(self, messages: List[BaseMessage]) -> Dict[str, Any]:
        """
        Invoke the workflow with the given messages
        
        Args:
            messages: The input messages
            
        Returns:
            The workflow output
        """
        try:
            # Initialize the state
            state = {
                "messages": messages,
                "is_last_step": False
            }
            
            # Run the workflow
            result = self.workflow.invoke(state)
            
            return result
        except Exception as e:
            logger.error(f"Error invoking workflow: {e}")
            raise RuntimeError(f"Error invoking workflow: {e}")
    
    def stream(self, messages: List[BaseMessage]):
        """
        Stream the workflow execution
        
        Args:
            messages: The input messages
            
        Yields:
            The workflow output at each step
        """
        try:
            # Initialize the state
            state = {
                "messages": messages,
                "is_last_step": False
            }
            
            # Stream the workflow
            for output in self.workflow.stream(state):
                yield output
        except Exception as e:
            logger.error(f"Error streaming workflow: {e}")
            raise RuntimeError(f"Error streaming workflow: {e}")
    
    def get_available_patterns(self) -> List[str]:
        """Get a list of available Fabric patterns"""
        return self.fabric_tools.get_available_patterns()
    
    def get_pattern_description(self, pattern: str) -> str:
        """Get a description of a specific Fabric pattern"""
        return self.fabric_tools.get_pattern_description(pattern)
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools"""
        return self.fabric_tools.get_tool_descriptions()