"""Client for communicating with OpenAI-compatible VLM/LLM APIs."""

import base64
import logging
import time

import requests

from config import (
    API_BASE_URL,
    API_KEY,
    DEFAULT_MODEL,
    MAX_TOKENS,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

# Rate-limit retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF = 2.0  # seconds, doubles each retry


class VLMClient:
    """Client for OpenAI-compatible VLM/LLM APIs (Mistral, LMStudio, etc.)."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = REQUEST_TIMEOUT,
        api_key: str = API_KEY,
        temperature: float = 0.7,
    ):
        """
        Initialize the VLM client.

        Args:
            base_url (str): API server URL
            model (str): Model identifier to use
            timeout (int): Request timeout in seconds
            api_key (str): API key for authentication (empty string = no auth)
            temperature (float): Sampling temperature for responses
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.api_key = api_key
        self.temperature = temperature
        self.chat_endpoint = f"{self.base_url}/chat/completions"

    def _build_headers(self) -> dict[str, str]:
        """
        Build request headers, including auth if API key is set.

        Returns:
            dict[str, str]: HTTP headers for API requests
        """
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def query(self, prompt: str, max_tokens: int = MAX_TOKENS) -> str:
        """
        Send a prompt to the VLM API and return the response.

        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int): Maximum tokens in the response

        Returns:
            str: The LLM's response text

        Raises:
            ConnectionError: If the VLM API is not reachable or auth fails
            requests.RequestException: For other HTTP errors
        """
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }

        try:
            # Retry loop for rate limiting
            for attempt in range(MAX_RETRIES):
                response = requests.post(
                    self.chat_endpoint,
                    json=payload,
                    headers=self._build_headers(),
                    timeout=self.timeout,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        wait = RETRY_BACKOFF * (2**attempt)
                        logger.warning(
                            f"Rate limited. Retrying in {wait}s "
                            f"(attempt {attempt + 1}/{MAX_RETRIES})"
                        )
                        time.sleep(wait)
                        continue
                    else:
                        raise requests.HTTPError(f"Rate limit exceeded after {MAX_RETRIES} retries")

                # Break retry loop on non-429 response
                break

            # Handle auth failures
            if response.status_code in (401, 403):
                raise ConnectionError(
                    f"Authentication failed for {self.base_url}. "
                    "Check your API key in .env or --api-key flag."
                )

            response.raise_for_status()

            data = response.json()
            content: str = data["choices"][0]["message"]["content"]
            return content

        except requests.ConnectionError as e:
            raise ConnectionError(
                f"Cannot connect to VLM API at {self.base_url}. "
                "Ensure the VLM API server is reachable."
            ) from e

    def is_available(self) -> bool:
        """
        Check if the VLM API server is available.

        Returns:
            bool: True if server is reachable, False otherwise
        """
        try:
            response = requests.get(
                f"{self.base_url}/models",
                headers=self._build_headers(),
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
            ConnectionError: If VLM API server is not reachable or auth fails
            ValueError: If image encoding fails
            requests.RequestException: For other HTTP errors
        """
        logger.info(f"Sending multimodal query to VLM (image size: {len(image_bytes)} bytes)")

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
                "temperature": self.temperature,
            }

            # Retry loop for rate limiting
            for attempt in range(MAX_RETRIES):
                response = requests.post(
                    self.chat_endpoint,
                    json=payload,
                    headers=self._build_headers(),
                    timeout=self.timeout,
                )

                # Handle rate limiting
                if response.status_code == 429:
                    if attempt < MAX_RETRIES - 1:
                        wait = RETRY_BACKOFF * (2**attempt)
                        logger.warning(
                            f"Rate limited. Retrying in {wait}s "
                            f"(attempt {attempt + 1}/{MAX_RETRIES})"
                        )
                        time.sleep(wait)
                        continue
                    else:
                        raise requests.HTTPError(f"Rate limit exceeded after {MAX_RETRIES} retries")

                # Break retry loop on non-429 response
                break

            # Handle auth failures
            if response.status_code in (401, 403):
                raise ConnectionError(
                    f"Authentication failed for {self.base_url}. "
                    "Check your API key in .env or --api-key flag."
                )

            response.raise_for_status()

            # Extract response text
            response_data = response.json()
            response_text: str = response_data["choices"][0]["message"]["content"]

            logger.info(f"Received VLM response ({len(response_text)} characters)")
            return response_text

        except requests.ConnectionError as e:
            logger.error(f"Failed to connect to VLM API: {e}")
            raise ConnectionError(
                f"Could not connect to VLM API at {self.base_url}. "
                "Ensure the VLM API server is reachable."
            ) from e
        except Exception as e:
            if "base64" in str(type(e).__name__).lower():
                logger.error(f"Failed to encode image: {e}")
                raise ValueError("Failed to encode image to base64") from e
            logger.error(f"VLM multimodal request failed: {e}")
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
