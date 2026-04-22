"""Unit tests for VLMClient class."""

import base64
import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
import requests

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

from vlm_client import MAX_RETRIES, RETRY_BACKOFF, VLMClient

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_successful_response() -> MagicMock:
    """Create a mock response matching OpenAI chat completion format."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {
        "choices": [{"message": {"content": "Test response"}}]
    }
    response.raise_for_status = MagicMock()
    return response


@pytest.fixture
def mock_rate_limit_response() -> MagicMock:
    """Create a mock 429 response."""
    response = MagicMock()
    response.status_code = 429
    return response


@pytest.fixture
def mock_auth_error_401_response() -> MagicMock:
    """Create a mock 401 response."""
    response = MagicMock()
    response.status_code = 401
    return response


@pytest.fixture
def mock_auth_error_403_response() -> MagicMock:
    """Create a mock 403 response."""
    response = MagicMock()
    response.status_code = 403
    return response


# ============================================================================
# Initialization Tests
# ============================================================================


def test_init_defaults() -> None:
    """VLMClient initializes with config defaults."""
    import config

    client = VLMClient()
    assert client.base_url == config.API_BASE_URL.rstrip("/")
    assert client.model == config.DEFAULT_MODEL
    assert client.timeout == config.REQUEST_TIMEOUT
    assert client.api_key == config.API_KEY
    assert client.temperature == 0.7


def test_init_custom_params() -> None:
    """VLMClient accepts custom parameters."""
    client = VLMClient(
        base_url="https://custom.api.com/v1",
        model="custom-model",
        timeout=60,
        api_key="sk-test-key",
        temperature=0.5,
    )
    assert client.base_url == "https://custom.api.com/v1"
    assert client.model == "custom-model"
    assert client.timeout == 60
    assert client.api_key == "sk-test-key"
    assert client.temperature == 0.5


def test_init_strips_trailing_slash() -> None:
    """base_url trailing slash is stripped."""
    client = VLMClient(base_url="https://api.example.com/v1/")
    assert client.base_url == "https://api.example.com/v1"


def test_init_chat_endpoint_constructed() -> None:
    """Chat endpoint is properly constructed from base_url."""
    client = VLMClient(base_url="https://api.example.com/v1", provider="mistral")
    assert client.chat_endpoint == "https://api.example.com/v1/chat/completions"


# ============================================================================
# Header Tests
# ============================================================================


def test_build_headers_with_api_key() -> None:
    """Headers include Bearer token when API key is set."""
    client = VLMClient(api_key="sk-test-123", provider="mistral")
    headers = client._build_headers()
    assert headers["Authorization"] == "Bearer sk-test-123"
    assert headers["Content-Type"] == "application/json"


def test_build_headers_without_api_key() -> None:
    """Headers omit Authorization when API key is empty."""
    client = VLMClient(api_key="")
    headers = client._build_headers()
    assert "Authorization" not in headers
    assert headers["Content-Type"] == "application/json"


# ============================================================================
# Query Tests (Mocked)
# ============================================================================


def test_query_success(mocker: Any, mock_successful_response: MagicMock) -> None:
    """query() sends correct payload and returns response text."""
    mock_post = mocker.patch("requests.post", return_value=mock_successful_response)

    client = VLMClient(
        base_url="https://api.test.com",
        model="test-model",
        temperature=0.8,
        provider="mistral",
    )
    result = client.query("test prompt", max_tokens=100, system_prompt="sys")

    assert result == "Test response"

    # Verify payload structure
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert payload["model"] == "test-model"
    assert payload["messages"][0] == {"role": "system", "content": "sys"}
    assert payload["messages"][1] == {"role": "user", "content": "test prompt"}
    assert payload["max_tokens"] == 100
    assert payload["temperature"] == 0.8


def test_query_sends_headers(mocker: Any, mock_successful_response: MagicMock) -> None:
    """query() includes auth headers in the request."""
    mock_post = mocker.patch("requests.post", return_value=mock_successful_response)

    client = VLMClient(api_key="sk-test-key", provider="mistral")
    client.query("test prompt", system_prompt="sys")

    # Verify headers were passed
    call_kwargs = mock_post.call_args[1]
    headers = call_kwargs["headers"]
    assert headers["Authorization"] == "Bearer sk-test-key"
    assert headers["Content-Type"] == "application/json"


def test_query_custom_temperature(
    mocker: Any, mock_successful_response: MagicMock
) -> None:
    """Temperature from constructor is used in request payload."""
    mock_post = mocker.patch("requests.post", return_value=mock_successful_response)

    client = VLMClient(temperature=0.3, provider="mistral")
    client.query("test", system_prompt="sys")

    # Verify temperature matches client.temperature (not hardcoded 0.7)
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert payload["temperature"] == 0.3


def test_query_multimodal_success(
    mocker: Any, mock_successful_response: MagicMock
) -> None:
    """query_multimodal() sends image as base64 in correct format."""
    mock_post = mocker.patch("requests.post", return_value=mock_successful_response)

    client = VLMClient(provider="mistral")
    test_image = b"fake-image-data"
    result = client.query_multimodal("describe this", test_image, system_prompt="sys")

    assert result == "Test response"

    # Verify payload contains image_url with data:image/png;base64, prefix
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    # First message is system, second is user
    message_content = payload["messages"][1]["content"]

    assert len(message_content) == 2
    assert message_content[0] == {"type": "text", "text": "describe this"}
    assert message_content[1]["type"] == "image_url"
    assert message_content[1]["image_url"]["url"].startswith("data:image/png;base64,")


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_query_connection_error(mocker: Any) -> None:
    """ConnectionError raised when server is unreachable."""
    mocker.patch(
        "requests.post", side_effect=requests.ConnectionError("Connection refused")
    )

    client = VLMClient()
    with pytest.raises(ConnectionError, match="Cannot connect to VLM API"):
        client.query("test", system_prompt="sys")


def test_query_auth_error_401(
    mocker: Any, mock_auth_error_401_response: MagicMock
) -> None:
    """HTTP 401 raises ConnectionError with auth message."""
    mocker.patch("requests.post", return_value=mock_auth_error_401_response)

    client = VLMClient()
    with pytest.raises(ConnectionError, match="Authentication failed"):
        client.query("test", system_prompt="sys")


def test_query_auth_error_403(
    mocker: Any, mock_auth_error_403_response: MagicMock
) -> None:
    """HTTP 403 raises ConnectionError with auth message."""
    mocker.patch("requests.post", return_value=mock_auth_error_403_response)

    client = VLMClient()
    with pytest.raises(ConnectionError, match="Authentication failed"):
        client.query("test", system_prompt="sys")


def test_query_multimodal_connection_error(mocker: Any) -> None:
    """query_multimodal() raises ConnectionError when server unreachable."""
    mocker.patch(
        "requests.post", side_effect=requests.ConnectionError("Connection refused")
    )

    client = VLMClient()
    with pytest.raises(ConnectionError, match="Could not connect to VLM API"):
        client.query_multimodal("test", b"image-data", system_prompt="sys")


# ============================================================================
# Rate-Limit Retry Tests
# ============================================================================


def test_query_rate_limit_retry_success(
    mocker: Any,
    mock_rate_limit_response: MagicMock,
    mock_successful_response: MagicMock,
) -> None:
    """HTTP 429 triggers retry, succeeds on second attempt."""
    mock_post = mocker.patch(
        "requests.post",
        side_effect=[mock_rate_limit_response, mock_successful_response],
    )
    mock_sleep = mocker.patch("time.sleep")

    client = VLMClient(provider="mistral")
    result = client.query("test", system_prompt="sys")

    assert result == "Test response"
    assert mock_post.call_count == 2
    # Verify time.sleep was called with correct backoff
    mock_sleep.assert_called_once_with(RETRY_BACKOFF * (2**0))


def test_query_rate_limit_exhausted(
    mocker: Any, mock_rate_limit_response: MagicMock
) -> None:
    """HTTP 429 on all retries raises HTTPError."""
    mocker.patch("requests.post", return_value=mock_rate_limit_response)
    mock_sleep = mocker.patch("time.sleep")

    client = VLMClient()
    with pytest.raises(
        requests.HTTPError, match=f"Rate limit exceeded after {MAX_RETRIES} retries"
    ):
        client.query("test", system_prompt="sys")

    # Verify sleep was called MAX_RETRIES-1 times (not on last attempt)
    assert mock_sleep.call_count == MAX_RETRIES - 1


def test_query_rate_limit_backoff_doubles(
    mocker: Any,
    mock_rate_limit_response: MagicMock,
) -> None:
    """Rate limit backoff doubles each retry."""
    mocker.patch("requests.post", return_value=mock_rate_limit_response)
    mock_sleep = mocker.patch("time.sleep")

    client = VLMClient()
    with pytest.raises(requests.HTTPError):
        client.query("test", system_prompt="sys")

    # Verify exponential backoff: 2.0, 4.0
    expected_sleeps = [RETRY_BACKOFF * (2**i) for i in range(MAX_RETRIES - 1)]
    actual_sleeps = [call[0][0] for call in mock_sleep.call_args_list]
    assert actual_sleeps == expected_sleeps


def test_query_multimodal_rate_limit_retry(
    mocker: Any,
    mock_rate_limit_response: MagicMock,
    mock_successful_response: MagicMock,
) -> None:
    """query_multimodal() also retries on HTTP 429."""
    mock_post = mocker.patch(
        "requests.post",
        side_effect=[mock_rate_limit_response, mock_successful_response],
    )
    mock_sleep = mocker.patch("time.sleep")

    client = VLMClient(provider="mistral")
    result = client.query_multimodal("test", b"image-data", system_prompt="sys")

    assert result == "Test response"
    assert mock_post.call_count == 2
    mock_sleep.assert_called_once()


# ============================================================================
# Health Check Tests
# ============================================================================


def test_is_available_success(mocker: Any) -> None:
    """is_available() returns True when server responds 200."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get = mocker.patch("requests.get", return_value=mock_response)

    client = VLMClient(base_url="https://api.test.com", provider="mistral")
    assert client.is_available() is True

    # Verify endpoint
    mock_get.assert_called_once()
    call_args = mock_get.call_args[0]
    assert call_args[0] == "https://api.test.com/models"


def test_is_available_failure(mocker: Any) -> None:
    """is_available() returns False when server is unreachable."""
    mocker.patch(
        "requests.get", side_effect=requests.RequestException("Connection failed")
    )

    client = VLMClient(provider="mistral")
    assert client.is_available() is False


def test_is_available_non_200_status(mocker: Any) -> None:
    """is_available() returns False for non-200 status codes."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mocker.patch("requests.get", return_value=mock_response)

    client = VLMClient(provider="mistral")
    assert client.is_available() is False


def test_is_available_sends_headers(mocker: Any) -> None:
    """is_available() includes auth headers."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get = mocker.patch("requests.get", return_value=mock_response)

    client = VLMClient(api_key="sk-test-key", provider="mistral")
    client.is_available()

    # Verify headers were passed
    call_kwargs = mock_get.call_args[1]
    headers = call_kwargs["headers"]
    assert headers["Authorization"] == "Bearer sk-test-key"


# ============================================================================
# Image Encoding Tests
# ============================================================================


def test_encode_image_to_base64() -> None:
    """_encode_image_to_base64 produces correct data URL."""
    client = VLMClient()
    test_bytes = b"test-image-bytes"
    result = client._encode_image_to_base64(test_bytes)

    assert result.startswith("data:image/png;base64,")

    # Verify base64 decodes back to original bytes
    base64_part = result.split(",")[1]
    decoded = base64.b64decode(base64_part)
    assert decoded == test_bytes


def test_encode_image_to_base64_empty() -> None:
    """_encode_image_to_base64 handles empty bytes."""
    client = VLMClient()
    result = client._encode_image_to_base64(b"")

    assert result == "data:image/png;base64,"


# ============================================================================
# Integration Tests (mocked but full flow)
# ============================================================================


def test_full_query_workflow(mocker: Any, mock_successful_response: MagicMock) -> None:
    """Test complete query workflow from initialization to response."""
    mock_post = mocker.patch("requests.post", return_value=mock_successful_response)

    client = VLMClient(
        base_url="https://api.test.com",
        model="test-model",
        api_key="sk-test",
        temperature=0.5,
        provider="mistral",
    )

    result = client.query("hello world", max_tokens=50, system_prompt="sys")

    assert result == "Test response"

    # Verify complete request structure
    mock_post.assert_called_once()
    call_args, call_kwargs = mock_post.call_args

    assert call_args[0] == "https://api.test.com/chat/completions"
    assert call_kwargs["json"]["model"] == "test-model"
    assert call_kwargs["json"]["temperature"] == 0.5
    assert call_kwargs["json"]["max_tokens"] == 50
    assert call_kwargs["headers"]["Authorization"] == "Bearer sk-test"


def test_full_multimodal_workflow(
    mocker: Any, mock_successful_response: MagicMock
) -> None:
    """Test complete multimodal workflow from initialization to response."""
    mock_post = mocker.patch("requests.post", return_value=mock_successful_response)

    client = VLMClient(
        base_url="https://api.test.com",
        model="vision-model",
        api_key="sk-vision",
        temperature=0.2,
        provider="mistral",
    )

    test_image = b"image-bytes-data"
    result = client.query_multimodal(
        "what is this?", test_image, max_tokens=200, system_prompt="sys"
    )

    assert result == "Test response"

    # Verify complete request structure
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]

    assert payload["model"] == "vision-model"
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 200

    # messages[0] = system, messages[1] = user with image content
    message_content = payload["messages"][1]["content"]
    assert message_content[0]["text"] == "what is this?"
    assert "data:image/png;base64," in message_content[1]["image_url"]["url"]


# ============================================================================
# Anthropic Provider Tests
# ============================================================================


def test_build_headers_anthropic_has_x_api_key() -> None:
    """Anthropic headers use x-api-key, not Authorization: Bearer."""
    client = VLMClient(
        provider="anthropic",
        api_key="em-anthropic-test-key",
        base_url="https://api.anthropic.com/v1",
    )
    headers = client._build_headers()

    assert headers["x-api-key"] == "em-anthropic-test-key"
    assert "Authorization" not in headers
    assert headers["Content-Type"] == "application/json"


def test_build_headers_anthropic_has_version() -> None:
    """Anthropic headers include the anthropic-version field."""
    client = VLMClient(
        provider="anthropic",
        api_key="em-anthropic-test-key",
        base_url="https://api.anthropic.com/v1",
    )
    headers = client._build_headers()

    assert "anthropic-version" in headers
    assert headers["anthropic-version"] == "2023-06-01"


def test_build_headers_anthropic_no_bearer_token() -> None:
    """Anthropic headers must not include any Authorization header."""
    client = VLMClient(
        provider="anthropic",
        api_key="em-anthropic-test-key",
        base_url="https://api.anthropic.com/v1",
    )
    headers = client._build_headers()

    assert "Authorization" not in headers


def test_build_text_payload_anthropic_structure() -> None:
    """Anthropic text payload follows Messages API format."""
    client = VLMClient(
        provider="anthropic",
        model="claude-sonnet-4-6",
        temperature=0.5,
        base_url="https://api.anthropic.com/v1",
    )
    payload = client._build_text_payload(
        "hello world", max_tokens=512, system_prompt="test system"
    )

    assert payload["model"] == "claude-sonnet-4-6"
    assert payload["max_tokens"] == 512
    assert payload["temperature"] == 0.5
    assert "messages" in payload
    assert len(payload["messages"]) == 1
    assert payload["messages"][0]["role"] == "user"
    assert payload["messages"][0]["content"] == "hello world"


def test_build_multimodal_payload_anthropic_image_block() -> None:
    """Anthropic multimodal payload uses type=image with source dict."""
    client = VLMClient(
        provider="anthropic",
        model="claude-sonnet-4-6",
        base_url="https://api.anthropic.com/v1",
    )
    test_image = b"fake-image-data"
    payload = client._build_multimodal_payload(
        "describe this", test_image, max_tokens=256, system_prompt="sys"
    )

    message_content = payload["messages"][0]["content"]
    assert len(message_content) == 2

    text_block = message_content[0]
    image_block = message_content[1]

    # Text block is first
    assert text_block["type"] == "text"
    assert text_block["text"] == "describe this"

    # Image block uses type=image (not image_url)
    assert image_block["type"] == "image"
    assert "image_url" not in image_block

    # Source dict structure
    source = image_block["source"]
    assert source["type"] == "base64"
    assert source["media_type"] == "image/png"
    assert "data" in source

    # Raw base64 — no data URL prefix
    assert not source["data"].startswith("data:image/png;base64,")
    decoded = base64.b64decode(source["data"])
    assert decoded == test_image


def test_build_multimodal_payload_anthropic_image_before_text() -> None:
    """Text block appears before the image block in Anthropic payload."""
    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
    )
    payload = client._build_multimodal_payload(
        "prompt text", b"img", max_tokens=100, system_prompt="sys"
    )
    content = payload["messages"][0]["content"]

    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image"


def test_extract_response_text_anthropic_format() -> None:
    """_extract_response_text correctly parses Anthropic content block response."""
    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
    )
    response_data = {"content": [{"type": "text", "text": "hello"}]}
    result = client._extract_response_text(response_data)

    assert result == "hello"


def test_query_anthropic_mock_http(mocker: Any) -> None:
    """query() with Anthropic provider sends correct headers and parses response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"content": [{"type": "text", "text": "result"}]}
    mock_response.raise_for_status = MagicMock()
    mock_post = mocker.patch("requests.post", return_value=mock_response)

    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        model="claude-sonnet-4-6",
        api_key="sk-ant-test",
    )
    result = client.query("test prompt", max_tokens=100, system_prompt="sys")

    assert result == "result"

    call_kwargs = mock_post.call_args[1]
    assert call_kwargs["headers"]["x-api-key"] == "sk-ant-test"
    assert call_kwargs["headers"]["anthropic-version"] == "2023-06-01"
    assert "Authorization" not in call_kwargs["headers"]
    assert mock_post.call_args[0][0] == "https://api.anthropic.com/v1/messages"


def test_query_multimodal_anthropic_mock_http(mocker: Any) -> None:
    """query_multimodal() with Anthropic sends correct image block structure."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "content": [{"type": "text", "text": "image description"}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_post = mocker.patch("requests.post", return_value=mock_response)

    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        model="claude-sonnet-4-6",
        api_key="sk-ant-test",
    )
    test_image = b"png-bytes"
    result = client.query_multimodal("what is shown?", test_image, system_prompt="sys")

    assert result == "image description"

    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    # Anthropic: messages[0] is the sole user message
    content = payload["messages"][0]["content"]

    # Text block first, image block second
    assert content[0]["type"] == "text"
    assert content[1]["type"] == "image"
    assert content[1]["source"]["type"] == "base64"
    assert content[1]["source"]["media_type"] == "image/png"


def test_query_anthropic_rate_limit_retries(mocker: Any) -> None:
    """Anthropic HTTP 429 triggers exponential backoff and retries."""
    mock_429 = MagicMock()
    mock_429.status_code = 429

    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.json.return_value = {"content": [{"type": "text", "text": "ok"}]}
    mock_200.raise_for_status = MagicMock()

    mock_post = mocker.patch("requests.post", side_effect=[mock_429, mock_200])
    mock_sleep = mocker.patch("time.sleep")

    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        api_key="sk-ant-test",
    )
    result = client.query("prompt", system_prompt="sys")

    assert result == "ok"
    assert mock_post.call_count == 2
    mock_sleep.assert_called_once_with(RETRY_BACKOFF * (2**0))


def test_query_anthropic_auth_failure_401(mocker: Any) -> None:
    """Anthropic HTTP 401 raises ConnectionError without crashing."""
    mock_401 = MagicMock()
    mock_401.status_code = 401
    mocker.patch("requests.post", return_value=mock_401)

    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        api_key="invalid-key",
    )
    with pytest.raises(ConnectionError, match="Authentication failed"):
        client.query("test prompt", system_prompt="sys")


# ============================================================================
# Multi-Image Payload Tests
# ============================================================================


def test_multi_image_payload_anthropic() -> None:
    """_build_multi_image_payload() builds correct Anthropic format for 3 images."""
    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        model="claude-sonnet-4-6",
        temperature=0.5,
    )
    images = [
        (b"image-bytes-1", "Label One"),
        (b"image-bytes-2", "Label Two"),
        (b"image-bytes-3", "Label Three"),
    ]
    payload = client._build_multi_image_payload(
        "main prompt", images, max_tokens=256, system_prompt="sys"
    )

    # Anthropic: messages[0] is the sole user message
    content = payload["messages"][0]["content"]

    # 3 images × (1 label + 1 image) + 1 prompt = 7 blocks
    assert len(content) == 7

    # Verify Anthropic image block structure for each image
    image_blocks = [block for block in content if block["type"] == "image"]
    assert len(image_blocks) == 3
    for image_block in image_blocks:
        assert "image_url" not in image_block
        source = image_block["source"]
        assert source["type"] == "base64"
        assert source["media_type"] == "image/png"
        assert "data" in source

    # Final block is the prompt
    assert content[-1]["type"] == "text"
    assert content[-1]["text"] == "main prompt"


def test_multi_image_payload_openai_compat() -> None:
    """_build_multi_image_payload() builds correct OpenAI-compat format for 3 images."""
    client = VLMClient(
        provider="mistral",
        base_url="https://api.mistral.ai/v1",
        model="pixtral-12b",
        temperature=0.7,
    )
    images = [
        (b"image-bytes-1", "Label One"),
        (b"image-bytes-2", "Label Two"),
        (b"image-bytes-3", "Label Three"),
    ]
    payload = client._build_multi_image_payload(
        "main prompt", images, max_tokens=256, system_prompt="sys"
    )

    # OpenAI-compat: messages[0]=system, messages[1]=user with image content
    content = payload["messages"][1]["content"]

    # 3 images × (1 label + 1 image_url) + 1 prompt = 7 blocks
    assert len(content) == 7

    # Verify OpenAI image_url block structure
    image_url_blocks = [block for block in content if block["type"] == "image_url"]
    assert len(image_url_blocks) == 3
    for image_url_block in image_url_blocks:
        assert "source" not in image_url_block
        assert "image_url" in image_url_block
        assert image_url_block["image_url"]["url"].startswith("data:image/png;base64,")

    # Label text block precedes each image_url block
    for i in range(3):
        label_idx = i * 2
        image_idx = i * 2 + 1
        assert content[label_idx]["type"] == "text"
        assert content[image_idx]["type"] == "image_url"

    # Final block is the prompt
    assert content[-1]["type"] == "text"
    assert content[-1]["text"] == "main prompt"


def test_multi_image_labels_present() -> None:
    """Each label string appears in the text block immediately before its image."""
    client = VLMClient(provider="mistral", base_url="https://api.mistral.ai/v1")
    images = [
        (b"img-a", "Canvas before stroke"),
        (b"img-b", "Reference artwork"),
        (b"img-c", "Style target"),
    ]
    payload = client._build_multi_image_payload(
        "describe differences", images, max_tokens=128, system_prompt="sys"
    )
    # OpenAI-compat: user content is at messages[1]
    content = payload["messages"][1]["content"]

    # Check that each label appears in the correct position
    assert content[0]["type"] == "text" and content[0]["text"] == "Canvas before stroke"
    assert content[2]["type"] == "text" and content[2]["text"] == "Reference artwork"
    assert content[4]["type"] == "text" and content[4]["text"] == "Style target"


def test_multi_image_empty_list() -> None:
    """_build_multi_image_payload() with empty images list produces only the prompt block."""
    client = VLMClient(provider="anthropic", base_url="https://api.anthropic.com/v1")
    payload = client._build_multi_image_payload(
        "just a prompt", [], max_tokens=64, system_prompt="sys"
    )

    # Anthropic: messages[0] is the sole user message
    content = payload["messages"][0]["content"]

    # Only 1 block: the prompt text
    assert len(content) == 1
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "just a prompt"


# ============================================================================
# System Prompt Placement Tests
# ============================================================================


def test_anthropic_system_prompt_is_content_block_array() -> None:
    """Anthropic: system_prompt is placed in payload['system'] as a content block list."""
    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
        model="claude-sonnet-4-6",
    )
    payload = client._build_text_payload(
        "user msg", max_tokens=100, system_prompt="Be helpful."
    )

    assert "system" in payload
    system = payload["system"]
    assert isinstance(system, list), "system must be a list of content blocks"
    assert len(system) == 1
    block = system[0]
    assert block["type"] == "text"
    assert block["text"] == "Be helpful."
    assert block["cache_control"] == {"type": "ephemeral"}


def test_anthropic_system_prompt_no_top_level_cache_control() -> None:
    """Anthropic payload must NOT have a top-level cache_control key."""
    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
    )
    payload = client._build_text_payload("msg", max_tokens=50, system_prompt="sys")
    assert "cache_control" not in payload


def test_anthropic_system_prompt_messages_no_system_role() -> None:
    """Anthropic: messages list must NOT contain a role=system entry."""
    client = VLMClient(
        provider="anthropic",
        base_url="https://api.anthropic.com/v1",
    )
    payload = client._build_text_payload("msg", max_tokens=50, system_prompt="sys")
    for msg in payload["messages"]:
        assert msg.get("role") != "system", (
            "Anthropic messages must not have role=system"
        )


def test_mistral_system_prompt_first_message() -> None:
    """Mistral: first message in payload['messages'] is role=system with system_prompt."""
    client = VLMClient(provider="mistral", base_url="https://api.mistral.ai/v1")
    payload = client._build_text_payload(
        "user question", max_tokens=100, system_prompt="You are an expert."
    )

    assert "system" not in payload, (
        "Mistral payload must NOT have a top-level system field"
    )
    assert payload["messages"][0] == {
        "role": "system",
        "content": "You are an expert.",
    }
    assert payload["messages"][1] == {"role": "user", "content": "user question"}


def test_lmstudio_system_prompt_first_message() -> None:
    """LMStudio (OpenAI-compat): first message is role=system with system_prompt."""
    client = VLMClient(provider="lmstudio", base_url="http://localhost:1234/v1")
    payload = client._build_text_payload(
        "user question", max_tokens=100, system_prompt="You are an expert."
    )

    assert "system" not in payload, (
        "LMStudio payload must NOT have a top-level system field"
    )
    assert payload["messages"][0] == {
        "role": "system",
        "content": "You are an expert.",
    }


def test_anthropic_multimodal_image_on_user_message_not_system() -> None:
    """Anthropic multimodal: image block is in the user message, not the system field."""
    client = VLMClient(provider="anthropic", base_url="https://api.anthropic.com/v1")
    payload = client._build_multimodal_payload(
        "describe", b"imgbytes", max_tokens=100, system_prompt="sys"
    )
    # system field is a text-only list
    for block in payload["system"]:
        assert block["type"] == "text", "system content blocks must be text"
    # user message contains the image
    user_content = payload["messages"][0]["content"]
    image_blocks = [b for b in user_content if b["type"] == "image"]
    assert len(image_blocks) == 1


def test_mistral_multimodal_image_on_user_message_not_system() -> None:
    """Mistral multimodal: image block is in the user message, not the system message."""
    client = VLMClient(provider="mistral", base_url="https://api.mistral.ai/v1")
    payload = client._build_multimodal_payload(
        "describe", b"imgbytes", max_tokens=100, system_prompt="sys"
    )
    # system message has plain string content
    assert payload["messages"][0]["role"] == "system"
    assert isinstance(payload["messages"][0]["content"], str)
    # user message contains the image
    user_content = payload["messages"][1]["content"]
    image_blocks = [b for b in user_content if b["type"] == "image_url"]
    assert len(image_blocks) == 1


def test_anthropic_multi_image_image_on_user_message() -> None:
    """Anthropic multi-image: image blocks are in the user message, not system."""
    client = VLMClient(provider="anthropic", base_url="https://api.anthropic.com/v1")
    images = [(b"img1", "Label 1"), (b"img2", "Label 2")]
    payload = client._build_multi_image_payload(
        "prompt", images, max_tokens=100, system_prompt="sys"
    )
    # system field is text-only
    for block in payload["system"]:
        assert block["type"] == "text"
    # user message has image blocks
    user_content = payload["messages"][0]["content"]
    image_blocks = [b for b in user_content if b["type"] == "image"]
    assert len(image_blocks) == 2


# ============================================================================
# cached_images Tests (Phase 27c)
# ============================================================================


def test_anthropic_cached_images_prepended_to_user_message() -> None:
    """Anthropic: cached_images appear before dynamic images in the user message."""
    client = VLMClient(provider="anthropic", base_url="https://api.anthropic.com/v1")
    cached = [
        (b"sample-1", "LINE stroke sample"),
        (b"sample-2", "ARC stroke sample"),
    ]
    dynamic = [(b"canvas-bytes", "Current canvas")]
    payload = client._build_multi_image_payload(
        "user prompt",
        dynamic,
        max_tokens=100,
        system_prompt="system text",
        cached_images=cached,
    )

    content = payload["messages"][0]["content"]
    # 2 cached × (label + image) + 1 dynamic × (label + image) + 1 prompt = 7 blocks
    assert len(content) == 7
    assert content[0] == {"type": "text", "text": "LINE stroke sample"}
    assert content[1]["type"] == "image"
    assert content[2] == {"type": "text", "text": "ARC stroke sample"}
    assert content[3]["type"] == "image"
    assert content[4] == {"type": "text", "text": "Current canvas"}
    assert content[5]["type"] == "image"
    assert content[6] == {"type": "text", "text": "user prompt"}


def test_anthropic_cached_images_cache_control_on_last_cached_block() -> None:
    """Anthropic: cache_control marker is on the last cached image block only."""
    client = VLMClient(provider="anthropic", base_url="https://api.anthropic.com/v1")
    cached = [
        (b"s1", "L1"),
        (b"s2", "L2"),
        (b"s3", "L3"),
    ]
    payload = client._build_multi_image_payload(
        "p",
        [(b"canvas", "Current canvas")],
        max_tokens=50,
        system_prompt="sys",
        cached_images=cached,
    )

    content = payload["messages"][0]["content"]
    # Image blocks at indices 1, 3, 5 (cached) and 7 (canvas, dynamic)
    cached_image_blocks = [content[1], content[3], content[5]]
    dynamic_image_block = content[7]

    # Only the LAST cached image block carries cache_control
    assert "cache_control" not in cached_image_blocks[0]
    assert "cache_control" not in cached_image_blocks[1]
    assert cached_image_blocks[2]["cache_control"] == {"type": "ephemeral"}

    # Dynamic canvas image must NOT carry cache_control
    assert dynamic_image_block["type"] == "image"
    assert "cache_control" not in dynamic_image_block


def test_anthropic_cached_images_none_unchanged_behaviour() -> None:
    """Anthropic: cached_images=None gives the original (dynamic-only) layout."""
    client = VLMClient(provider="anthropic", base_url="https://api.anthropic.com/v1")
    payload = client._build_multi_image_payload(
        "prompt",
        [(b"img", "label")],
        max_tokens=100,
        system_prompt="sys",
        cached_images=None,
    )

    content = payload["messages"][0]["content"]
    # Just label + image + prompt
    assert len(content) == 3
    assert content[0] == {"type": "text", "text": "label"}
    assert content[1]["type"] == "image"
    assert "cache_control" not in content[1]
    assert content[2] == {"type": "text", "text": "prompt"}


def test_openai_compat_cached_images_prepended_without_cache_control() -> None:
    """Mistral/LMStudio: cached_images are prepended but carry no cache marker."""
    client = VLMClient(provider="mistral", base_url="https://api.mistral.ai/v1")
    cached = [(b"sample-1", "LINE stroke sample")]
    payload = client._build_multi_image_payload(
        "user prompt",
        [(b"canvas", "Current canvas")],
        max_tokens=100,
        system_prompt="system text",
        cached_images=cached,
    )

    # System lives in messages[0] for OpenAI-compat
    assert payload["messages"][0]["role"] == "system"
    assert payload["messages"][0]["content"] == "system text"

    user_content = payload["messages"][1]["content"]
    # cached label+image + dynamic label+image + prompt = 5 blocks
    assert len(user_content) == 5
    assert user_content[0] == {"type": "text", "text": "LINE stroke sample"}
    assert user_content[1]["type"] == "image_url"
    assert user_content[2] == {"type": "text", "text": "Current canvas"}
    assert user_content[3]["type"] == "image_url"
    assert user_content[4] == {"type": "text", "text": "user prompt"}

    # OpenAI-compat image_url blocks have no cache_control field
    for block in user_content:
        assert "cache_control" not in block


def test_anthropic_system_block_keeps_cache_control_with_cached_images() -> None:
    """Anthropic: system block retains its own cache_control independent of cached_images."""
    client = VLMClient(provider="anthropic", base_url="https://api.anthropic.com/v1")
    payload = client._build_multi_image_payload(
        "p",
        [(b"c", "Current canvas")],
        max_tokens=50,
        system_prompt="sys",
        cached_images=[(b"s", "Sample")],
    )

    assert payload["system"][0]["cache_control"] == {"type": "ephemeral"}
