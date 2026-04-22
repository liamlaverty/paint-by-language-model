"""Client for communicating with OpenAI-compatible VLM/LLM APIs."""

import base64
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import cast

import requests

from config import (
    ANTHROPIC_VERSION,
    API_BASE_URL,
    API_KEY,
    DEFAULT_MODEL,
    GLOBAL_PROMPT_LOG_DIR,
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

        # Stores the raw ``usage`` dict from the most recent successful API
        # response so callers can inspect token counts (e.g. for caching tests).
        self.last_usage: dict | None = None

        # Set endpoint based on provider
        if self.provider == "anthropic":
            self.chat_endpoint = f"{self.base_url}/messages"
        else:
            self.chat_endpoint = f"{self.base_url}/chat/completions"

    def _log_request(
        self,
        endpoint: str,
        headers: dict[str, str],
        payload: dict,
        response: "requests.Response",
    ) -> None:
        """
        Write a request/response log file to GLOBAL_PROMPT_LOG_DIR.

        Sensitive header values (x-api-key, authorization) are masked before
        writing so that API keys are never stored in plaintext.

        Args:
            endpoint (str): The URL the request was sent to
            headers (dict[str, str]): Request headers (will be masked before logging)
            payload (dict): Request body sent to the API
            response (requests.Response): The HTTP response received
        """
        now = datetime.now()
        log_dir = (
            Path(GLOBAL_PROMPT_LOG_DIR) / f"{now.year:04d}" / f"{now.month:02d}" / f"{now.day:02d}"
        )
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        log_path = log_dir / f"{timestamp}-request.log"

        # Mask sensitive header values
        safe_headers = {
            k: ("***" if k.lower() in ("x-api-key", "authorization") else v)
            for k, v in headers.items()
        }

        try:
            response_body = json.dumps(response.json(), indent=2)
        except Exception:
            response_body = str(response.text)

        log_content = "\n".join(
            [
                f"=== VLM Request Log: {timestamp} ===",
                f"Endpoint: {endpoint}",
                "Headers:",
                json.dumps(safe_headers, indent=2),
                "Payload:",
                json.dumps(payload, indent=2),
                "--- Response ---",
                f"Status: {response.status_code}",
                "Body:",
                response_body,
            ]
        )

        try:
            log_path.write_text(log_content, encoding="utf-8")
            logger.debug("Request logged to %s", log_path)
        except OSError as e:
            logger.warning("Failed to write request log: %s", e)

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

    def _build_text_payload(self, prompt: str, max_tokens: int, *, system_prompt: str) -> dict:
        """
        Build request payload for text-only query based on provider.

        Args:
            prompt (str): The text prompt to send
            max_tokens (int): Maximum tokens in the response
            system_prompt (str): System-level instructions; provider-agnostic.
                Anthropic: placed in top-level ``system`` field as a content block
                array with block-level ``cache_control``. OpenAI-compatible
                providers: prepended as a ``role: system`` message.

        Returns:
            dict: Request payload structure for the API
        """

        payload: dict = {}

        payload["model"] = self.model

        if self.provider == "anthropic":
            payload["system"] = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
            payload["messages"] = [{"role": "user", "content": prompt}]
        else:
            payload["messages"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ]

        payload["max_tokens"] = max_tokens
        payload["temperature"] = self.temperature

        return payload

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

    def query(self, prompt: str, max_tokens: int = MAX_TOKENS, *, system_prompt: str) -> str:
        """
        Send a prompt to the VLM API and return the response.

        Args:
            prompt (str): The prompt to send to the LLM
            max_tokens (int): Maximum tokens in the response
            system_prompt (str): System-level instructions sent to the model.
                Required keyword-only argument. Anthropic: placed in the
                top-level ``system`` field as a content block with
                ``cache_control``. OpenAI-compatible providers: prepended as
                the first ``role: system`` message.

        Returns:
            str: The LLM's response text

        Raises:
            ConnectionError: If the VLM API is not reachable or auth fails
            requests.RequestException: For other HTTP errors
        """
        payload = self._build_text_payload(prompt, max_tokens, system_prompt=system_prompt)

        try:
            # Retry loop for rate limiting
            for attempt in range(MAX_RETRIES):
                _headers = self._build_headers()
                response = requests.post(
                    self.chat_endpoint,
                    json=payload,
                    headers=_headers,
                    timeout=self.timeout,
                )

                # log the raw request and response for debugging
                self._log_request(self.chat_endpoint, _headers, payload, response)

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
            self.last_usage = data.get("usage")
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
                payload = self._build_text_payload("test", 1, system_prompt="")
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

    def _build_multimodal_payload(
        self, prompt: str, image_bytes: bytes, max_tokens: int, *, system_prompt: str
    ) -> dict:
        """
        Build request payload for multimodal query based on provider.

        Args:
            prompt (str): The text prompt to send with the image
            image_bytes (bytes): Image data as bytes
            max_tokens (int): Maximum tokens in the response
            system_prompt (str): System-level instructions; provider-agnostic.
                Anthropic: placed in top-level ``system`` field as a content
                block array with block-level ``cache_control``. OpenAI-compatible
                providers: prepended as a ``role: system`` message.

        Returns:
            dict: Request payload structure for the API
        """
        if self.provider == "anthropic":
            # Anthropic uses raw base64 without data URL prefix
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            # Image block comes BEFORE text block (Anthropic best practice)
            message_content = [
                {"type": "text", "text": prompt},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64_image,
                    },
                },
            ]
        else:
            # OpenAI-compatible format uses data URL
            image_data_url = self._encode_image_to_base64(image_bytes)
            # Text block comes before image block
            message_content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_data_url}},
            ]

        payload: dict = {}
        payload["model"] = self.model

        if self.provider == "anthropic":
            payload["system"] = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
            payload["messages"] = [{"role": "user", "content": message_content}]
        else:
            payload["messages"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_content},
            ]

        payload["max_tokens"] = max_tokens
        payload["temperature"] = self.temperature

        return payload

    def query_multimodal(
        self, prompt: str, image_bytes: bytes, max_tokens: int = MAX_TOKENS, *, system_prompt: str
    ) -> str:
        """
        Send an image and text prompt to the VLM and return the response.

        Args:
            prompt (str): The text prompt to send with the image
            image_bytes (bytes): Image data as bytes (PNG, JPEG, etc.)
            max_tokens (int): Maximum tokens in response (default from config)
            system_prompt (str): System-level instructions sent to the model.
                Required keyword-only argument. Anthropic: placed in the
                top-level ``system`` field as a content block with
                ``cache_control``. OpenAI-compatible providers: prepended as
                the first ``role: system`` message.

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
            payload = self._build_multimodal_payload(
                prompt, image_bytes, max_tokens, system_prompt=system_prompt
            )

            # Retry loop for rate limiting
            for attempt in range(MAX_RETRIES):
                _headers = self._build_headers()
                response = requests.post(
                    self.chat_endpoint,
                    json=payload,
                    headers=_headers,
                    timeout=self.timeout,
                )

                # log the raw request and response for debugging
                self._log_request(self.chat_endpoint, _headers, payload, response)

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
            self.last_usage = response_data.get("usage")
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
        *,
        system_prompt: str,
        cached_images: list[tuple[bytes, str]] | None = None,
    ) -> dict:
        """
        Build request payload for a multi-image multimodal query.

        Each image is preceded by a text label block. A final text block
        containing the main prompt is appended after all image blocks.

        When ``cached_images`` is provided, those (image_bytes, label) pairs are
        prepended to the user message before the dynamic ``images``. On
        Anthropic, ``cache_control: ephemeral`` is placed on the **last cached
        image block**, telling Anthropic to cache the entire prompt prefix up
        to and including that block (system prompt + all cached images). The
        dynamic per-request ``images`` and the final prompt text follow and are
        not cached.

        Args:
            prompt (str): The main text prompt appended after all images
            images (list[tuple[bytes, str]]): Dynamic per-request
                (image_bytes, label) pairs that change between calls.
            max_tokens (int): Maximum tokens in the response
            system_prompt (str): System-level instructions; provider-agnostic.
                Anthropic: placed in top-level ``system`` field as a content
                block array with block-level ``cache_control``. OpenAI-compatible
                providers: prepended as a ``role: system`` message.
            cached_images (list[tuple[bytes, str]] | None): Optional list of
                static (image_bytes, label) pairs that are byte-identical
                across requests. Prepended to the user message before the
                dynamic ``images``. On Anthropic, the **last** of these image
                blocks carries ``cache_control: ephemeral`` to mark the cache
                prefix boundary. On OpenAI-compatible providers, they are
                still prepended (no cache marker — caching is Anthropic-only).

        Returns:
            dict: Request payload structure for the API
        """
        message_content: list[dict] = []

        # Prepend cached static images (with cache_control on the last image
        # block for Anthropic). Anthropic caches everything up to and
        # including the marked block, so the system prefix + all of these
        # images become the cache prefix.
        cached_list = cached_images or []
        for idx, (image_bytes, label) in enumerate(cached_list):
            base64_image = base64.b64encode(image_bytes).decode("utf-8")
            message_content.append({"type": "text", "text": label})
            is_last_cached = idx == len(cached_list) - 1
            if self.provider == "anthropic":
                image_block: dict = {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": base64_image,
                    },
                }
                if is_last_cached:
                    image_block["cache_control"] = {"type": "ephemeral"}
                message_content.append(image_block)
            else:
                # OpenAI-compatible: use data URL format, no cache support
                data_url = f"data:image/png;base64,{base64_image}"
                message_content.append({"type": "image_url", "image_url": {"url": data_url}})

        # Append dynamic per-request images
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

        payload: dict = {}
        payload["model"] = self.model

        if self.provider == "anthropic":
            # When cached_images are present, the cache breakpoint lives on
            # the last cached image block in the user message. The system
            # block keeps its own breakpoint for text-only / fallback cases,
            # which is harmless (Anthropic allows up to 4 breakpoints per
            # request and caches the longest matching prefix).
            payload["system"] = [
                {
                    "type": "text",
                    "text": system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
            payload["messages"] = [{"role": "user", "content": message_content}]
        else:
            payload["messages"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message_content},
            ]

        payload["max_tokens"] = max_tokens
        payload["temperature"] = self.temperature

        return payload

    def query_multimodal_multi_image(
        self,
        prompt: str,
        images: list[tuple[bytes, str]],
        max_tokens: int = MAX_TOKENS,
        *,
        system_prompt: str,
        cached_images: list[tuple[bytes, str]] | None = None,
    ) -> str:
        """
        Send multiple labelled images and a text prompt to the VLM in one request.

        Each image in ``images`` is a ``(image_bytes, label)`` pair. The label
        is inserted as a text block immediately before the corresponding image
        block, and the main prompt is appended as the final text block.

        Args:
            prompt (str): The main text prompt sent after all images
            images (list[tuple[bytes, str]]): Dynamic per-request
                (image_bytes, label) pairs that change between calls.
            max_tokens (int): Maximum tokens in response (default from config)
            system_prompt (str): System-level instructions sent to the model.
                Required keyword-only argument. Anthropic: placed in the
                top-level ``system`` field as a content block with
                ``cache_control``. OpenAI-compatible providers: prepended as
                the first ``role: system`` message.
            cached_images (list[tuple[bytes, str]] | None): Optional list of
                static images to include in the cached prompt prefix.
                Prepended to the user message. On Anthropic, ``cache_control``
                is placed on the last cached image block to mark the cache
                boundary. Ignored as a cache marker on OpenAI-compatible
                providers (still prepended for content parity).

        Returns:
            str: The VLM's response text

        Raises:
            ConnectionError: If VLM API server is not reachable or auth fails
            ValueError: If image encoding fails
            requests.RequestException: For other HTTP errors
        """
        cached_count = len(cached_images) if cached_images else 0
        total_bytes = sum(len(img_bytes) for img_bytes, _ in images)
        cached_bytes = sum(len(img_bytes) for img_bytes, _ in cached_images) if cached_images else 0
        logger.info(
            f"Sending multi-image query to VLM "
            f"({len(images)} dynamic images / {total_bytes} bytes; "
            f"{cached_count} cached images / {cached_bytes} bytes)"
        )

        try:
            payload = self._build_multi_image_payload(
                prompt,
                images,
                max_tokens,
                system_prompt=system_prompt,
                cached_images=cached_images,
            )

            # Retry loop for rate limiting
            for attempt in range(MAX_RETRIES):
                _headers = self._build_headers()
                response = requests.post(
                    self.chat_endpoint,
                    json=payload,
                    headers=_headers,
                    timeout=self.timeout,
                )

                # log the raw request and response for debugging
                self._log_request(self.chat_endpoint, _headers, payload, response)

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
            self.last_usage = response_data.get("usage")
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
