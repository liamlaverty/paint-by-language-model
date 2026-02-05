"""Client for communicating with LMStudio's OpenAI-compatible API."""

import base64
import logging

import requests

from config import (
    LMSTUDIO_BASE_URL,
    LMSTUDIO_MODEL,
    MAX_TOKENS,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)


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
            base_url (str): LMStudio server URL
            model (str): Model identifier to use
            timeout (int): Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.chat_endpoint = f"{self.base_url}/chat/completions"

    def query(self, prompt: str, max_tokens: int = MAX_TOKENS) -> str:
        """
        Send a prompt to LMStudio and return the response.

        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int): Maximum tokens in the response

        Returns:
            str: The LLM's response text

        Raises:
            ConnectionError: If LMStudio is not running or unreachable
            requests.RequestException: For other HTTP errors
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
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
            content: str = data["choices"][0]["message"]["content"]
            return content

        except requests.ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to LMStudio at {self.base_url}. "
                "Ensure LMStudio is running with the local server enabled."
            ) from e

    def is_available(self) -> bool:
        """
        Check if LMStudio server is available.

        Returns:
            bool: True if server is reachable, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                timeout=5,
            )
            return response.status_code == 200
        except requests.RequestException:
            return False

    def query_multimodal(
        self, prompt: str, image_bytes: bytes, max_tokens: int = MAX_TOKENS
    ) -> str:
        """
        Send an image and text prompt to the VLM and return the response.

        Args:
            prompt (str): The text prompt to send with the image
            image_bytes (bytes): Image data as bytes (PNG, JPEG, etc.)
            max_tokens (int): Maximum tokens in response (default from config)

        Returns:
            str: The VLM's response text

        Raises:
            ConnectionError: If LMStudio server is not reachable
            ValueError: If image encoding fails
            requests.RequestException: For other HTTP errors
        """
        logger.info(
            f"Sending multimodal query to LMStudio VLM (image size: {len(image_bytes)} bytes)"
        )

        try:
            # Encode image to base64
            image_data_url = self._encode_image_to_base64(image_bytes)

            # Build multimodal message content
            message_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]

            # Build request payload
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": message_content}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            }

            # Send request
            response = requests.post(self.chat_endpoint, json=payload, timeout=self.timeout)
            response.raise_for_status()

            # Extract response text
            response_data = response.json()
            response_text: str = response_data["choices"][0]["message"]["content"]

            logger.info(f"Received VLM response ({len(response_text)} characters)")
            return response_text

        except requests.ConnectionError as e:
            logger.error(f"Failed to connect to LMStudio: {e}")
            raise ConnectionError(
                f"Could not connect to LMStudio at {self.base_url}. "
                "Make sure LMStudio is running with the server enabled."
            ) from e
        except Exception as e:
            if "base64" in str(type(e).__name__).lower():
                logger.error(f"Failed to encode image: {e}")
                raise ValueError("Failed to encode image to base64") from e
            logger.error(f"LMStudio multimodal request failed: {e}")
            raise

    def _encode_image_to_base64(self, image_bytes: bytes) -> str:
        """
        Encode image bytes to base64 data URL format.

        Args:
            image_bytes (bytes): Raw image bytes

        Returns:
            str: Base64-encoded data URL
        """
        base64_image = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/png;base64,{base64_image}"
