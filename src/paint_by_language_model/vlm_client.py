"""Client for communicating with OpenAI-compatible VLM/LLM APIs."""

import base64
import logging
import time
from typing import cast

import requests

from config import (
    ANTHROPIC_VERSION,
    API_BASE_URL,
    API_KEY,
    DEFAULT_MODEL,
    MAX_TOKENS,
    PROVIDER,
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
        provider: str = PROVIDER,
    ):
        """
        Initialize the VLM client.

        Args:
            base_url (str): API server URL
            model (str): Model identifier to use
            timeout (int): Request timeout in seconds
            api_key (str): API key for authentication (empty string = no auth)
            temperature (float): Sampling temperature for responses
            provider (str): API provider ("mistral", "lmstudio", or "anthropic")
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.api_key = api_key
        self.temperature = temperature
        self.provider = provider

        # Set endpoint based on provider
        if self.provider == "anthropic":
            self.chat_endpoint = f"{self.base_url}/messages"
        else:
            self.chat_endpoint = f"{self.base_url}/chat/completions"

    def _build_headers(self) -> dict[str, str]:
        """
        Build request headers, including auth if API key is set.

        Returns:
            dict[str, str]: HTTP headers for API requests
        """
        headers = {"Content-Type": "application/json"}
        if self.provider == "anthropic":
            if self.api_key:
                headers["x-api-key"] = self.api_key
            headers["anthropic-version"] = ANTHROPIC_VERSION
        else:
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_text_payload(self, prompt: str, max_tokens: int) -> dict:
        """
        Build request payload for text-only query based on provider.

        Args:
            prompt (str): The text prompt to send
            max_tokens (int): Maximum tokens in the response

        Returns:
            dict: Request payload structure for the API
        """
        # Text-only message format is identical for all providers
        return {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }

    def _extract_response_text(self, response_data: dict) -> str:
        """
        Extract text content from API response based on provider.

        Args:
            response_data (dict): JSON response from the API

        Returns:
            str: Extracted text content
        """
        if self.provider == "anthropic":
            return cast(str, response_data["content"][0]["text"])
        else:
            return cast(str, response_data["choices"][0]["message"]["content"])

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
        payload = self._build_text_payload(prompt, max_tokens)

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
            content: str = self._extract_response_text(data)
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
            if self.provider == "anthropic":
                # Anthropic doesn't document GET /v1/models, so perform a minimal message call
                logger.debug("Checking Anthropic API availability with minimal message call")
                payload = self._build_text_payload("test", 1)
                response = requests.post(
                    self.chat_endpoint,
                    json=payload,
                    headers=self._build_headers(),
                    timeout=5,
                )
                return response.status_code in range(200, 300)
            else:
                # OpenAI-compatible providers support GET /v1/models
                response = requests.get(
                    f"{self.base_url}/models",
                    headers=self._build_headers(),
                    timeout=5,
                )
                return response.status_code == 200
        except requests.RequestException:
            return False

    def _build_multimodal_payload(self, prompt: str, image_bytes: bytes, max_tokens: int) -> dict:
        """
        Build request payload for multimodal query based on provider.

        Args:
            prompt (str): The text prompt to send with the image
            image_bytes (bytes): Image data as bytes
            max_tokens (int): Maximum tokens in the response

        Returns:
            dict: Request payload structure for the API
        """
        if self.provider == "anthropic":
            # Anthropic uses raw base64 without data URL prefix
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            # Image block comes BEFORE text block (Anthropic best practice)
            message_content = [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64_image,
                    },
                },
                {"type": "text", "text": prompt},
            ]
        else:
            # OpenAI-compatible format uses data URL
            image_data_url = self._encode_image_to_base64(image_bytes)
            # Text block comes before image block
            message_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]

        return {
            "model": self.model,
            "messages": [{"role": "user", "content": message_content}],
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }

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
            # Build provider-specific multimodal payload
            payload = self._build_multimodal_payload(prompt, image_bytes, max_tokens)

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

            # Extract response text using provider-specific parsing
            response_data = response.json()
            response_text: str = self._extract_response_text(response_data)

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

    def _build_multi_image_payload(
        self,
        prompt: str,
        images: list[tuple[bytes, str]],
        max_tokens: int,
    ) -> dict:
        """
        Build request payload for a multi-image multimodal query.

        Each image is preceded by a text label block. A final text block
        containing the main prompt is appended after all image blocks.

        Args:
            prompt (str): The main text prompt appended after all images
            images (list[tuple[bytes, str]]): List of (image_bytes, label) pairs
            max_tokens (int): Maximum tokens in the response

        Returns:
            dict: Request payload structure for the API
        """
        message_content: list[dict] = []

        for image_bytes, label in images:
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            # Label block before each image
            message_content.append({"type": "text", "text": label})
            if self.provider == "anthropic":
                message_content.append(
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image,
                        },
                    }
                )
            else:
                # OpenAI-compatible: use data URL format
                data_url = f"data:image/png;base64,{base64_image}"
                message_content.append({"type": "image_url", "image_url": {"url": data_url}})

        # Append main prompt as final text block
        message_content.append({"type": "text", "text": prompt})

        return {
            "model": self.model,
            "messages": [{"role": "user", "content": message_content}],
            "max_tokens": max_tokens,
            "temperature": self.temperature,
        }

    def query_multimodal_multi_image(
        self,
        prompt: str,
        images: list[tuple[bytes, str]],
        max_tokens: int = MAX_TOKENS,
    ) -> str:
        """
        Send multiple labelled images and a text prompt to the VLM in one request.

        Each image in ``images`` is a ``(image_bytes, label)`` pair. The label
        is inserted as a text block immediately before the corresponding image
        block, and the main prompt is appended as the final text block.

        Args:
            prompt (str): The main text prompt sent after all images
            images (list[tuple[bytes, str]]): List of (image_bytes, label) pairs
            max_tokens (int): Maximum tokens in response (default from config)

        Returns:
            str: The VLM's response text

        Raises:
            ConnectionError: If VLM API server is not reachable or auth fails
            ValueError: If image encoding fails
            requests.RequestException: For other HTTP errors
        """
        total_bytes = sum(len(img_bytes) for img_bytes, _ in images)
        logger.info(
            f"Sending multi-image query to VLM ({len(images)} images, {total_bytes} total bytes)"
        )

        try:
            payload = self._build_multi_image_payload(prompt, images, max_tokens)

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

            response_data = response.json()
            response_text: str = self._extract_response_text(response_data)

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
            logger.error(f"VLM multi-image request failed: {e}")
            raise
