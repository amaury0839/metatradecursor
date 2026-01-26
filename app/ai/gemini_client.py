"""Google Gemini API client with safety fallback"""

import json
import re
import hashlib
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai
from app.core.config import get_config
from app.core.logger import setup_logger

logger = setup_logger("gemini_client")


def safe_parse_gemini_json(text: str) -> Optional[Dict[str, Any]]:
    """Extract and parse the first JSON object from text; tolerant to truncation."""
    if not text:
        return None

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    json_text = match.group(0)
    try:
        return json.loads(json_text)
    except json.JSONDecodeError:
        return None


def safe_gemini_text(response) -> Optional[str]:
    """Extract text from Gemini response with safety checks.
    
    Returns None if response is blocked by safety filters.
    This prevents crashes when Gemini refuses to respond.
    """
    try:
        if not response:
            return None
        
        # Check if blocked by safety filters
        if hasattr(response, 'prompt_feedback'):
            if response.prompt_feedback.block_reason:
                logger.warning(f"Gemini blocked by safety: {response.prompt_feedback.block_reason}")
                return None
        
        # Try to get text
        if hasattr(response, 'text'):
            return response.text.strip()
        
        # Check candidates
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                if candidate.content.parts:
                    return candidate.content.parts[0].text.strip()
        
        logger.warning("Could not extract text from Gemini response")
        return None
        
    except Exception as e:
        logger.error(f"Error extracting Gemini text: {e}")
        return None


class GeminiClient:
    """Client for Google Gemini API"""
    
    def __init__(self):
        self.config = get_config()
        self.model = None
        self._prompt_cache: Dict[str, Dict[str, Any]] = {}  # hash -> response
        
        # Skip Gemini initialization if API key is not configured
        if not self.config.ai.gemini_api_key:
            logger.warning("GEMINI_API_KEY not configured - AI features disabled in cloud")
            return
            
        try:
            genai.configure(api_key=self.config.ai.gemini_api_key)
            # Get model from config or use default
            primary_model = getattr(self.config.ai, "gemini_model", "gemini-2.0-pro-exp-02-05")
            fallback_models = [
                primary_model,
                "gemini-2.0-pro-exp-02-05",
                "gemini-2.5-pro",
                "gemini-2-flash-exp",
                "gemini-1.5-flash",
                "gemini-pro",
            ]
            
            # Try models in order
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
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.model = None
    
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
            # Contract: force strict JSON or explicit unavailable sentinel
            contract = (
                "Devuelve EXCLUSIVAMENTE un JSON VÁLIDO. "
                "No incluyas texto fuera del JSON, ni markdown, ni comentarios. "
                "Si no puedes generar el JSON completo, devuelve exactamente {\"status\":\"unavailable\"}. "
                "Schema esperado: {\n"
                "  \"action\": \"HOLD\",\n"
                "  \"confidence\": 0.0,\n"
                "  \"market_bias\": \"neutral\",\n"
                "  \"summary\": \"string\"\n"
                "}"
            )

            # Combine prompts under contract
            full_prompt = f"{contract}\n\n{system_prompt}\n\n{user_prompt}"
            
            # Generate response
            if self.model is None:
                logger.warning("Gemini model not available, returning None for fallback")
                return None
            
            response = self.model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.2,  # Low temp = more deterministic, less blocks
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": 512,  # Reduced for faster, safer responses
                }
            )
            
            # Parse response with safety check
            response_text = safe_gemini_text(response)
            
            # Fallback if blocked
            if response_text is None:
                logger.warning("Gemini response blocked or empty - using neutral fallback")
                return {
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reason": ["Market analysis unavailable due to API restrictions"],
                    "reasoning": "Market analysis unavailable due to API restrictions. Gemini safety filter activated.",
                    "market_bias": "neutral",
                    "probability_up": 0.5,
                    "risk_ok": False,
                    "sources": []
                }
            
            # Try to extract JSON robustly
            result = safe_parse_gemini_json(response_text)
            if not result or result.get("status") == "unavailable":
                logger.warning("Gemini JSON invalid or unavailable")
                return {
                    "action": "HOLD",
                    "confidence": 0.0,
                    "reasoning": "Gemini unavailable or returned invalid JSON.",
                    "market_bias": "neutral",
                    "probability_up": 0.5,
                    "risk_ok": False,
                    "sources": [],
                }

            if use_cache:
                self._prompt_cache[prompt_hash] = result

            logger.debug("Gemini response parsed successfully")
            return result
                
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
