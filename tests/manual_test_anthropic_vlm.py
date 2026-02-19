"""Manual integration test for Anthropic VLM API connectivity and queries.

Usage:
    conda activate paint-by-language-model
    ANTHROPIC_API_KEY=sk-ant-... python tests/manual_test_anthropic_vlm.py

Prerequisites:
    - Set ANTHROPIC_API_KEY in your .env file or as an environment variable.
    - Ensure the paint-by-language-model conda environment is active.

This script tests:
    1. Anthropic API connectivity via is_available()
    2. Text-only query via query()
    3. Multimodal query with a synthetic test image via query_multimodal()
"""

import logging
import os
import sys
from io import BytesIO
from pathlib import Path

# Add source root to path
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

import config
from vlm_client import VLMClient

# Configure logging to stdout for manual runs
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def _create_test_image_bytes() -> bytes:
    """
    Create a minimal PNG image in memory for multimodal testing.

    Returns:
        bytes: PNG image bytes suitable for encoding and sending to the API.
    """
    try:
        from PIL import Image

        img = Image.new("RGB", (64, 64), color=(100, 149, 237))  # cornflower blue
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Fallback: return a valid 1×1 white PNG (minimal valid PNG bytes)
        logger.warning("PIL not available; using minimal 1×1 PNG fallback")
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18"
            b"\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )


def _make_anthropic_client() -> VLMClient:
    """
    Build a VLMClient configured for the Anthropic provider.

    Returns:
        VLMClient: Client pointing at the Anthropic Messages API.
    """
    return VLMClient(
        provider="anthropic",
        base_url=config.ANTHROPIC_BASE_URL,
        model=config.ANTHROPIC_VLM_MODEL,
        api_key=config.ANTHROPIC_API_KEY,
    )


def test_connectivity() -> bool:
    """
    Test Anthropic API connectivity via is_available().

    Returns:
        bool: True if API is reachable and responds successfully.
    """
    logger.info("=== Test 1: Connectivity ===")
    client = _make_anthropic_client()
    logger.info("Checking Anthropic API availability at %s …", client.base_url)
    try:
        available = client.is_available()
        if available:
            logger.info("SUCCESS — Anthropic API is reachable")
        else:
            logger.error("FAILURE — is_available() returned False")
        return available
    except Exception as exc:
        logger.error("FAILURE — Exception during connectivity check: %s", exc)
        return False


def test_text_query() -> bool:
    """
    Test a text-only query to the Anthropic API.

    Sends a simple prompt about artistic style and validates that the response
    is a non-empty string.

    Returns:
        bool: True if a non-empty string response was received.
    """
    logger.info("=== Test 2: Text-only query ===")
    client = _make_anthropic_client()
    prompt = "In two sentences, describe the artistic style of Pablo Picasso."
    logger.info("Sending text prompt: %r", prompt)
    try:
        response = client.query(prompt, max_tokens=150)
        if not isinstance(response, str):
            logger.error("FAILURE — response is not a string: %r", type(response))
            return False
        if not response.strip():
            logger.error("FAILURE — response is empty")
            return False
        logger.info("SUCCESS — received %d characters", len(response))
        logger.info("Response preview: %s", response[:200])
        return True
    except Exception as exc:
        logger.error("FAILURE — Exception during text query: %s", exc)
        return False


def test_multimodal_query() -> bool:
    """
    Test a multimodal query with a test PNG image sent to the Anthropic API.

    Creates a synthetic image, encodes it, and sends it with a text prompt.
    Validates that the response is a non-empty string with no parsing errors.

    Returns:
        bool: True if a valid non-empty response was received.
    """
    logger.info("=== Test 3: Multimodal query ===")
    client = _make_anthropic_client()

    image_bytes = _create_test_image_bytes()
    logger.info("Created test image (%d bytes)", len(image_bytes))

    prompt = "Briefly describe the dominant colour in this image in one sentence."
    logger.info("Sending multimodal prompt: %r", prompt)
    try:
        response = client.query_multimodal(prompt, image_bytes, max_tokens=100)
        if not isinstance(response, str):
            logger.error("FAILURE — response is not a string: %r", type(response))
            return False
        if not response.strip():
            logger.error("FAILURE — response is empty")
            return False
        logger.info("SUCCESS — received %d characters", len(response))
        logger.info("Response preview: %s", response[:200])
        return True
    except Exception as exc:
        logger.error("FAILURE — Exception during multimodal query: %s", exc)
        return False


def validate_response_format(response: str) -> bool:
    """
    Validate that a VLM response is a plain string with no structural issues.

    Args:
        response (str): The response text returned by VLMClient.

    Returns:
        bool: True if response is a non-empty plain string.
    """
    if not isinstance(response, str):
        logger.warning("Response is not a str: %r", type(response))
        return False
    if not response.strip():
        logger.warning("Response is blank or whitespace-only")
        return False
    return True


def main() -> None:
    """
    Run all Anthropic VLM manual integration tests in sequence.

    Checks for ANTHROPIC_API_KEY before running and reports pass/fail for
    each test.  Does not raise exceptions — all outcomes are logged.
    """
    print("=" * 60)
    print("Anthropic VLM — Manual Integration Test")
    print("=" * 60)

    api_key = os.getenv("ANTHROPIC_API_KEY") or config.ANTHROPIC_API_KEY
    if not api_key:
        logger.error(
            "ANTHROPIC_API_KEY is not set. "
            "Set it in .env or as an environment variable before running this test."
        )
        sys.exit(1)

    logger.info("Using model: %s", config.ANTHROPIC_VLM_MODEL)
    logger.info("API endpoint: %s", config.ANTHROPIC_BASE_URL)

    results: dict[str, bool] = {}

    results["connectivity"] = test_connectivity()
    results["text_query"] = test_text_query()
    results["multimodal_query"] = test_multimodal_query()

    print("\n" + "=" * 60)
    print("Results:")
    all_passed = True
    for name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {name:<22} {status}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("All tests passed.")
    else:
        print("One or more tests FAILED — see log output above.")
    print("=" * 60)


if __name__ == "__main__":
    main()
