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
    client = VLMClient(base_url="https://api.example.com/v1")
    assert client.chat_endpoint == "https://api.example.com/v1/chat/completions"


# ============================================================================
# Header Tests
# ============================================================================


def test_build_headers_with_api_key() -> None:
    """Headers include Bearer token when API key is set."""
    client = VLMClient(api_key="sk-test-123")
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
        base_url="https://api.test.com", model="test-model", temperature=0.8
    )
    result = client.query("test prompt", max_tokens=100)

    assert result == "Test response"

    # Verify payload structure
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert payload["model"] == "test-model"
    assert payload["messages"] == [{"role": "user", "content": "test prompt"}]
    assert payload["max_tokens"] == 100
    assert payload["temperature"] == 0.8


def test_query_sends_headers(mocker: Any, mock_successful_response: MagicMock) -> None:
    """query() includes auth headers in the request."""
    mock_post = mocker.patch("requests.post", return_value=mock_successful_response)

    client = VLMClient(api_key="sk-test-key")
    client.query("test prompt")

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

    client = VLMClient(temperature=0.3)
    client.query("test")

    # Verify temperature matches client.temperature (not hardcoded 0.7)
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    assert payload["temperature"] == 0.3


def test_query_multimodal_success(
    mocker: Any, mock_successful_response: MagicMock
) -> None:
    """query_multimodal() sends image as base64 in correct format."""
    mock_post = mocker.patch("requests.post", return_value=mock_successful_response)

    client = VLMClient()
    test_image = b"fake-image-data"
    result = client.query_multimodal("describe this", test_image)

    assert result == "Test response"

    # Verify payload contains image_url with data:image/png;base64, prefix
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]
    message_content = payload["messages"][0]["content"]

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
        client.query("test")


def test_query_auth_error_401(
    mocker: Any, mock_auth_error_401_response: MagicMock
) -> None:
    """HTTP 401 raises ConnectionError with auth message."""
    mocker.patch("requests.post", return_value=mock_auth_error_401_response)

    client = VLMClient()
    with pytest.raises(ConnectionError, match="Authentication failed"):
        client.query("test")


def test_query_auth_error_403(
    mocker: Any, mock_auth_error_403_response: MagicMock
) -> None:
    """HTTP 403 raises ConnectionError with auth message."""
    mocker.patch("requests.post", return_value=mock_auth_error_403_response)

    client = VLMClient()
    with pytest.raises(ConnectionError, match="Authentication failed"):
        client.query("test")


def test_query_multimodal_connection_error(mocker: Any) -> None:
    """query_multimodal() raises ConnectionError when server unreachable."""
    mocker.patch(
        "requests.post", side_effect=requests.ConnectionError("Connection refused")
    )

    client = VLMClient()
    with pytest.raises(ConnectionError, match="Could not connect to VLM API"):
        client.query_multimodal("test", b"image-data")


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

    client = VLMClient()
    result = client.query("test")

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
        client.query("test")

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
        client.query("test")

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

    client = VLMClient()
    result = client.query_multimodal("test", b"image-data")

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

    client = VLMClient(base_url="https://api.test.com")
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

    client = VLMClient()
    assert client.is_available() is False


def test_is_available_non_200_status(mocker: Any) -> None:
    """is_available() returns False for non-200 status codes."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mocker.patch("requests.get", return_value=mock_response)

    client = VLMClient()
    assert client.is_available() is False


def test_is_available_sends_headers(mocker: Any) -> None:
    """is_available() includes auth headers."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get = mocker.patch("requests.get", return_value=mock_response)

    client = VLMClient(api_key="sk-test-key")
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
    )

    result = client.query("hello world", max_tokens=50)

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
    )

    test_image = b"image-bytes-data"
    result = client.query_multimodal("what is this?", test_image, max_tokens=200)

    assert result == "Test response"

    # Verify complete request structure
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]
    payload = call_kwargs["json"]

    assert payload["model"] == "vision-model"
    assert payload["temperature"] == 0.2
    assert payload["max_tokens"] == 200

    message_content = payload["messages"][0]["content"]
    assert message_content[0]["text"] == "what is this?"
    assert "data:image/png;base64," in message_content[1]["image_url"]["url"]
