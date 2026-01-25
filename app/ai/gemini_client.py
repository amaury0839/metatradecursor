"""Google Gemini API client"""

import json
import hashlib
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai
from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("gemini_client")


class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self):
        self.config = get_config()
        genai.configure(api_key=self.config.ai.gemini_api_key)
        # Get model from config or use default
        primary_model = getattr(self.config.ai, 'gemini_model', 'gemini-2-flash-exp')
        fallback_models = [
            primary_model,
            'gemini-2-flash-exp',
            'gemini-1.5-flash',
            'gemini-pro'
        ]
        
        # Try models in order
        self.model = None
        for model_name in fallback_models:
            try:
                self.model = genai.GenerativeModel(model_name)
                logger.info(f"Initialized with model: {model_name}")
                break
            except Exception as e:
                logger.debug(f"Model {model_name} not available: {e}")
                continue
        
        if self.model is None:
            logger.warning("No valid Gemini model available, using fallback logic")
            self.model = None  # Will trigger fallback in generate_content
        
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}  # hash -> response
    
    def generate_content(
        self, 
        system_prompt: str, 
        user_prompt: str,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Generate content from Gemini
        
        Args:
            system_prompt: System prompt
            user_prompt: User prompt
            use_cache: Whether to use cached responses
        
        Returns:
            Parsed JSON response or None
        """
        # Create prompt hash for caching
        prompt_hash = hashlib.md5(
            f"{system_prompt}{user_prompt}".encode()
        ).hexdigest()
        
        # Check cache
        if use_cache and prompt_hash in self._prompt_cache:
            logger.debug("Using cached Gemini response")
            return self._prompt_cache[prompt_hash]
        
        try:
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate response
            if self.model is None:
                logger.warning("Gemini model not available, returning None for fallback")
                return None
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.3,  # Lower temperature for more consistent outputs
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 1024,
                }
            )
            
            # Parse response
            response_text = response.text.strip()
            
            # Try to extract JSON from response (might be wrapped in markdown)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            # Parse JSON
            try:
                result = json.loads(response_text)
                
                # Cache result
                if use_cache:
                    self._prompt_cache[prompt_hash] = result
                
                logger.debug("Gemini response parsed successfully")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse Gemini JSON response: {e}")
                logger.error(f"Response text: {response_text[:500]}")
                return None
                
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}", exc_info=True)
            return None
    
    def clear_cache(self):
        """Clear prompt cache"""
        self._prompt_cache.clear()
        logger.debug("Gemini cache cleared")


# Global Gemini client instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get global Gemini client instance"""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
