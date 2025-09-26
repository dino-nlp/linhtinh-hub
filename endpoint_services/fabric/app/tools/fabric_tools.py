import logging
from typing import Dict, Any, Optional, List
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from ..core.fabric_integration import FabricIntegrationLayer, FabricPattern

logger = logging.getLogger(__name__)

class SummarizeInput(BaseModel):
    """Input schema for the summarize tool"""
    text: str = Field(description="The text to summarize")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options for summarization")

class AnalyzeClaimsInput(BaseModel):
    """Input schema for the analyze_claims tool"""
    text: str = Field(description="The text to analyze for claims")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options for claim analysis")

class ExtractWisdomInput(BaseModel):
    """Input schema for the extract_wisdom tool"""
    text: str = Field(description="The text to extract wisdom from")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options for wisdom extraction")

class ImproveWritingInput(BaseModel):
    """Input schema for the improve_writing tool"""
    text: str = Field(description="The text to improve")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options for writing improvement")

class TranslateInput(BaseModel):
    """Input schema for the translate tool"""
    text: str = Field(description="The text to translate")
    target_language: str = Field(description="The target language for translation")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Additional options for translation")

class SummarizeTool(BaseTool):
    """Tool for summarizing text using Fabric"""
    name: str = "summarize"
    description: str = "Summarize the input text using Fabric"
    args_schema: type = SummarizeInput
    
    def __init__(self, fabric_integration: FabricIntegrationLayer):
        super().__init__()
        self.fabric_integration = fabric_integration
    
    def _run(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Run the summarize tool"""
        try:
            return self.fabric_integration.summarize(text, options)
        except Exception as e:
            logger.error(f"Error in summarize tool: {e}")
            return f"Error summarizing text: {str(e)}"

class AnalyzeClaimsTool(BaseTool):
    """Tool for analyzing claims in text using Fabric"""
    name: str = "analyze_claims"
    description: str = "Analyze claims in the input text using Fabric"
    args_schema: type = AnalyzeClaimsInput
    
    def __init__(self, fabric_integration: FabricIntegrationLayer):
        super().__init__()
        self.fabric_integration = fabric_integration
    
    def _run(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Run the analyze_claims tool"""
        try:
            return self.fabric_integration.analyze_claims(text, options)
        except Exception as e:
            logger.error(f"Error in analyze_claims tool: {e}")
            return f"Error analyzing claims: {str(e)}"

class ExtractWisdomTool(BaseTool):
    """Tool for extracting wisdom from text using Fabric"""
    name: str = "extract_wisdom"
    description: str = "Extract wisdom from the input text using Fabric"
    args_schema: type = ExtractWisdomInput
    
    def __init__(self, fabric_integration: FabricIntegrationLayer):
        super().__init__()
        self.fabric_integration = fabric_integration
    
    def _run(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Run the extract_wisdom tool"""
        try:
            return self.fabric_integration.extract_wisdom(text, options)
        except Exception as e:
            logger.error(f"Error in extract_wisdom tool: {e}")
            return f"Error extracting wisdom: {str(e)}"

class ImproveWritingTool(BaseTool):
    """Tool for improving writing using Fabric"""
    name: str = "improve_writing"
    description: str = "Improve the writing in the input text using Fabric"
    args_schema: type = ImproveWritingInput
    
    def __init__(self, fabric_integration: FabricIntegrationLayer):
        super().__init__()
        self.fabric_integration = fabric_integration
    
    def _run(self, text: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Run the improve_writing tool"""
        try:
            return self.fabric_integration.improve_writing(text, options)
        except Exception as e:
            logger.error(f"Error in improve_writing tool: {e}")
            return f"Error improving writing: {str(e)}"

class TranslateTool(BaseTool):
    """Tool for translating text using Fabric"""
    name: str = "translate"
    description: str = "Translate the input text to a target language using Fabric"
    args_schema: type = TranslateInput
    
    def __init__(self, fabric_integration: FabricIntegrationLayer):
        super().__init__()
        self.fabric_integration = fabric_integration
    
    def _run(self, text: str, target_language: str, options: Optional[Dict[str, Any]] = None) -> str:
        """Run the translate tool"""
        try:
            return self.fabric_integration.translate(text, target_language, options)
        except Exception as e:
            logger.error(f"Error in translate tool: {e}")
            return f"Error translating text: {str(e)}"

class FabricTools:
    """Collection of Fabric tools for Langchain"""
    
    def __init__(self, fabric_integration: FabricIntegrationLayer):
        self.fabric_integration = fabric_integration
        self._tools = None
    
    @property
    def tools(self) -> List[BaseTool]:
        """Get all available Fabric tools"""
        if self._tools is None:
            self._tools = [
                SummarizeTool(self.fabric_integration),
                AnalyzeClaimsTool(self.fabric_integration),
                ExtractWisdomTool(self.fabric_integration),
                ImproveWritingTool(self.fabric_integration),
                TranslateTool(self.fabric_integration)
            ]
        return self._tools
    
    def get_tool_by_name(self, name: str) -> Optional[BaseTool]:
        """Get a specific tool by name"""
        for tool in self.tools:
            if tool.name == name:
                return tool
        return None
    
    def get_tool_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all available tools"""
        return {tool.name: tool.description for tool in self.tools}
    
    def get_available_patterns(self) -> List[str]:
        """Get a list of available Fabric patterns"""
        return self.fabric_integration.get_available_patterns()
    
    def get_pattern_description(self, pattern: str) -> str:
        """Get a description of a specific Fabric pattern"""
        return self.fabric_integration.get_pattern_description(pattern)