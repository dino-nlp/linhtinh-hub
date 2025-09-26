import subprocess
import json
import logging
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)

class FabricPattern(Enum):
    """Available Fabric patterns"""
    SUMMARIZE = "summarize"
    ANALYZE_CLAIMS = "analyze_claims"
    EXTRACT_WISDOM = "extract_wisdom"
    IMPROVE_WRITING = "improve_writing"
    TRANSLATE = "translate"

class FabricIntegrationLayer:
    """
    Integration layer for communicating with Fabric CLI/API
    """
    
    def __init__(self, fabric_path: str = "fabric"):
        """
        Initialize the Fabric integration layer
        
        Args:
            fabric_path: Path to the Fabric CLI executable
        """
        self.fabric_path = fabric_path
        self._validate_fabric_installation()
    
    def _validate_fabric_installation(self) -> None:
        """Validate that Fabric CLI is installed and accessible"""
        try:
            result = subprocess.run(
                [self.fabric_path, "--version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Fabric CLI version: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Fabric CLI validation failed: {e}")
            raise RuntimeError("Fabric CLI is not installed or not accessible")
    
    def _run_fabric_command(
        self, 
        pattern: FabricPattern, 
        input_text: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Run a Fabric command with the specified pattern and input
        
        Args:
            pattern: The Fabric pattern to use
            input_text: The input text to process
            options: Additional options for the Fabric command
            
        Returns:
            The output from the Fabric command
        """
        cmd = [self.fabric_path, pattern.value]
        
        if options:
            for key, value in options.items():
                if isinstance(value, bool) and value:
                    cmd.append(f"--{key}")
                elif not isinstance(value, bool):
                    cmd.extend([f"--{key}", str(value)])
        
        try:
            logger.info(f"Running Fabric command: {' '.join(cmd)}")
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=input_text)
            
            if process.returncode != 0:
                logger.error(f"Fabric command failed with error: {stderr}")
                raise RuntimeError(f"Fabric command failed: {stderr}")
            
            return stdout
        except Exception as e:
            logger.error(f"Error running Fabric command: {e}")
            raise RuntimeError(f"Error running Fabric command: {e}")
    
    def summarize(
        self, 
        text: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Summarize the input text using Fabric
        
        Args:
            text: The text to summarize
            options: Additional options for the summarization
            
        Returns:
            The summarized text
        """
        return self._run_fabric_command(FabricPattern.SUMMARIZE, text, options)
    
    def analyze_claims(
        self, 
        text: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Analyze claims in the input text using Fabric
        
        Args:
            text: The text to analyze
            options: Additional options for the claim analysis
            
        Returns:
            The claim analysis result
        """
        return self._run_fabric_command(FabricPattern.ANALYZE_CLAIMS, text, options)
    
    def extract_wisdom(
        self, 
        text: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Extract wisdom from the input text using Fabric
        
        Args:
            text: The text to process
            options: Additional options for wisdom extraction
            
        Returns:
            The extracted wisdom
        """
        return self._run_fabric_command(FabricPattern.EXTRACT_WISDOM, text, options)
    
    def improve_writing(
        self, 
        text: str, 
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Improve the writing in the input text using Fabric
        
        Args:
            text: The text to improve
            options: Additional options for writing improvement
            
        Returns:
            The improved text
        """
        return self._run_fabric_command(FabricPattern.IMPROVE_WRITING, text, options)
    
    def translate(
        self, 
        text: str, 
        target_language: str,
        options: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Translate the input text using Fabric
        
        Args:
            text: The text to translate
            target_language: The target language for translation
            options: Additional options for translation
            
        Returns:
            The translated text
        """
        if options is None:
            options = {}
        options["target_language"] = target_language
        return self._run_fabric_command(FabricPattern.TRANSLATE, text, options)
    
    def get_available_patterns(self) -> List[str]:
        """
        Get a list of available Fabric patterns
        
        Returns:
            List of available pattern names
        """
        return [pattern.value for pattern in FabricPattern]
    
    def get_pattern_description(self, pattern: str) -> str:
        """
        Get a description of a specific Fabric pattern
        
        Args:
            pattern: The pattern name
            
        Returns:
            Description of the pattern
        """
        descriptions = {
            FabricPattern.SUMMARIZE.value: "Summarize the input text",
            FabricPattern.ANALYZE_CLAIMS.value: "Analyze claims in the input text",
            FabricPattern.EXTRACT_WISDOM.value: "Extract wisdom from the input text",
            FabricPattern.IMPROVE_WRITING.value: "Improve the writing in the input text",
            FabricPattern.TRANSLATE.value: "Translate the input text to a target language"
        }
        return descriptions.get(pattern, "Unknown pattern")