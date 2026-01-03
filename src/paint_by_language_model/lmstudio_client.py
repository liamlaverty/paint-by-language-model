"""Client for communicating with LMStudio's OpenAI-compatible API."""
import requests

from config import (
    LMSTUDIO_BASE_URL,
    LMSTUDIO_MODEL,
    REQUEST_TIMEOUT,
    MAX_TOKENS,
)


class LMStudioClient:
    """Client for the LMStudio local LLM API."""
    
    def __init__(
        self,
        base_url: str = LMSTUDIO_BASE_URL,
        model: str = LMSTUDIO_MODEL,
        timeout: int = REQUEST_TIMEOUT,
    ):
        """
        Initialize the LMStudio client.
        
        Args:
            base_url: LMStudio server URL
            model: Model identifier to use
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout
        self.chat_endpoint = f"{self.base_url}/chat/completions"
    
    def query(self, prompt: str, max_tokens: int = MAX_TOKENS) -> str:
        """
        Send a prompt to LMStudio and return the response.
        
        Args:
            prompt: The prompt to send to the LLM
            max_tokens: Maximum tokens in the response
            
        Returns:
            The LLM's response text
            
        Raises:
            ConnectionError: If LMStudio is not running or unreachable
            requests.RequestException: For other HTTP errors
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        
        try:
            response = requests.post(
                self.chat_endpoint,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except requests.ConnectionError:
            raise ConnectionError(
                f"Cannot connect to LMStudio at {self.base_url}. "
                "Ensure LMStudio is running with the local server enabled."
            )
    
    def is_available(self) -> bool:
        """
        Check if LMStudio server is available.
        
        Returns:
            True if server is reachable, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
