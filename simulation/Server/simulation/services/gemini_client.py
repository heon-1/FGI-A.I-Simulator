"""
Gemini AI Client for UX Simulation
"""
from typing import Optional
from django.conf import settings
from google import genai
from google.genai import types


class GeminiClient:
    """
    Wrapper for Google Gemini API with retry and safety features.
    """
    _instance: Optional['GeminiClient'] = None

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL
        self._client = None
        
        if self.api_key:
            self._client = genai.Client(api_key=self.api_key)

    @classmethod
    def get_instance(cls) -> 'GeminiClient':
        """Get singleton instance"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def generate(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """
        Generate content using Gemini API.
        
        Args:
            prompt: The user prompt
            system_instruction: Optional system instruction
            
        Returns:
            Generated text response
        """
        if not self._client:
            return self._fallback_generate(prompt)

        try:
            config = None
            if system_instruction:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction
                )

            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config
            )
            
            return response.text or ""
        except Exception as e:
            print(f"[GeminiClient] Error: {e}")
            return self._fallback_generate(prompt)

    def generate_stream(self, prompt: str, system_instruction: Optional[str] = None):
        """
        Generate content with streaming response.
        
        Yields:
            Text chunks as they are generated
        """
        if not self._client:
            yield self._fallback_generate(prompt)
            return

        try:
            config = None
            if system_instruction:
                config = types.GenerateContentConfig(
                    system_instruction=system_instruction
                )

            for chunk in self._client.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=config
            ):
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            print(f"[GeminiClient] Stream error: {e}")
            yield self._fallback_generate(prompt)

    @staticmethod
    def _fallback_generate(prompt: str) -> str:
        """Return a placeholder response when API is unavailable"""
        head = prompt[:120].replace("\n", " ")
        return f"[DEV_FALLBACK] Request: {head}..."


def get_gemini_client() -> GeminiClient:
    """Get Gemini client instance"""
    return GeminiClient.get_instance()
