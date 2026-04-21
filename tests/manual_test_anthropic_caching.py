"""Manual integration test for Anthropic prompt caching.

Verifies that prompt caching works correctly by inspecting the `usage` fields
in the API response. Sends two identical requests and asserts that the first
writes to cache (cache_creation_input_tokens > 0) and the second reads from
cache (cache_read_input_tokens > 0).

Usage:
    conda activate paint-by-language-model
    python tests/manual_test_anthropic_caching.py

Prerequisites:
    - Set ANTHROPIC_API_KEY in your .env file or as an environment variable.
    - Ensure the paint-by-language-model conda environment is active.

Notes:
    - Uses claude-3-haiku-20240307 (cheapest available model).
    - Requires a system prompt >= 2048 tokens to meet Haiku 3's caching minimum.
      Below this threshold caching is silently skipped with no error returned.
    - The 5-minute cache TTL means the second request must arrive within 5 minutes
      of the first for a cache hit to register.
"""

import json
import os
import sys
import time
from pathlib import Path

# Add source root to path (matches pattern used in other manual test files)
sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

import requests
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_API_VERSION = "2023-06-01"
MODEL = "claude-haiku-4-5"
USER_MESSAGE = "mary had a little"

# How long to wait between Request 1 and Request 2 (seconds).
# The cache is available as soon as the first response begins, but a small
# pause avoids any edge-case race conditions.
INTER_REQUEST_WAIT_SECONDS = 2


# ---------------------------------------------------------------------------
# Standalone helper functions (copied/adapted from vlm_client.py)
# ---------------------------------------------------------------------------


def build_headers(api_key: str) -> dict[str, str]:
    """
    Build Anthropic request headers.

    Args:
        api_key (str): Anthropic API key for authentication.

    Returns:
        dict[str, str]: HTTP headers for the Anthropic Messages API.
    """
    return {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": ANTHROPIC_API_VERSION,
    }


def build_payload(system_prompt: str) -> dict:
    """
    Build the request payload with block-level cache_control on the system prompt.

    Anthropic prompt caching requires ``cache_control`` to be placed on the
    specific content block to be cached, not at the top level of the payload.
    The ``system`` field must be an array of content blocks; adding
    ``cache_control: {"type": "ephemeral"}`` to a block tells Anthropic to
    cache up to and including that block.

    Args:
        system_prompt (str): The large static system prompt to cache.

    Returns:
        dict: Request payload ready to POST to the Anthropic Messages API.
    """
    return {
        "model": MODEL,
        "system": [
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        "messages": [{"role": "user", "content": USER_MESSAGE}],
        "max_tokens": 50,
        "temperature": 0.0,
    }


def send_request(api_key: str, payload: dict) -> dict:
    """
    POST the payload to the Anthropic Messages API and return the full JSON response.

    Args:
        api_key (str): Anthropic API key.
        payload (dict): Request body to send.

    Returns:
        dict: Full JSON response from the API.

    Raises:
        requests.HTTPError: If the API returns a non-2xx status code.
    """
    headers = build_headers(api_key)
    response = requests.post(
        ANTHROPIC_API_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()  # type: ignore[no-any-return]


# ---------------------------------------------------------------------------
# System prompt generator
# ---------------------------------------------------------------------------

# A single block of art-analysis instructional text (~150 words / ~200 tokens).
# Repeated enough times to exceed the 2048-token minimum for Claude Haiku 3.
_INSTRUCTION_BLOCK = (
    "You are an expert art analyst and historian with deep knowledge of painting "
    "techniques, art movements, and the lives of famous artists. Your role is to "
    "examine paintings in forensic detail, identifying brushwork, colour palette, "
    "composition, perspective, and stylistic signatures. When analysing a work you "
    "will consider the historical context in which it was created, the materials "
    "and pigments likely used, and how the piece fits within the broader canon of "
    "Western and non-Western art. You will compare the work to contemporaneous "
    "pieces and note influences the artist may have absorbed from their teachers, "
    "travelling companions, and rivals. Your commentary must be grounded in "
    "verifiable art-historical fact while remaining accessible to an educated "
    "general audience. Avoid speculation unless clearly labelled as such. Provide "
    "structured responses with sections for Composition, Technique, Colour, "
    "Historical Context, and Stylistic Significance. "
)

# 28 repetitions × ~200 tokens ≈ 5600 tokens — above the 4096-token minimum
# required for Claude Haiku 4.5. (Haiku 3 minimum was 2048 tokens; Haiku 4.5
# raised this threshold to 4096 tokens.)
_REPEAT_COUNT = 28


def generate_padding_system_prompt() -> str:
    """
    Return a deterministic static system prompt guaranteed to exceed 4096 tokens.

    Claude Haiku 4.5 requires at least 4096 tokens in a cacheable block for
    automatic prompt caching to activate (older Haiku 3 required 2048 tokens).
    The text is thematically consistent with the paint-by-language-model project.
    It is identical on every call so the Anthropic cache prefix hash matches
    between Request 1 and Request 2.

    Returns:
        str: Static instructional text of approximately 3200 tokens.
    """
    return _INSTRUCTION_BLOCK * _REPEAT_COUNT


# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


def test_cache_write_then_read(api_key: str) -> bool:
    """
    Prove Anthropic prompt caching works end-to-end.

    Sends two identical requests. Asserts that the first request writes content
    to the cache (cache_creation_input_tokens > 0) and the second request reads
    that content from the cache (cache_read_input_tokens > 0).

    Args:
        api_key (str): Anthropic API key.

    Returns:
        bool: True if both assertions pass, False otherwise.
    """
    print("\n=== Test: cache_write_then_read ===")

    system_prompt = generate_padding_system_prompt()
    estimated_words = len(system_prompt.split())
    # Rough token estimate: English averages ~0.75 words per token
    estimated_tokens = int(estimated_words / 0.75)
    print(f"System prompt length: ~{estimated_tokens} tokens ({estimated_words} words)")

    payload = build_payload(system_prompt)

    print(f"Payload keys: {', '.join(payload.keys())}")
    print(f'System prompt preview: "{system_prompt[:100]}..."')

    passed = True

    # ------------------------------------------------------------------
    # Request 1 — expect cache WRITE
    # ------------------------------------------------------------------
    print("\nRequest 1 (expect cache WRITE):")
    try:
        resp1 = send_request(api_key, payload)
    except requests.HTTPError as exc:
        print(f"  ERROR: HTTP {exc.response.status_code} — {exc.response.text}")
        return False

    usage1 = resp1.get("usage", {})
    print(f"  usage: {json.dumps(usage1)}")

    required_keys = {
        "input_tokens",
        "cache_creation_input_tokens",
        "cache_read_input_tokens",
    }
    missing = required_keys - usage1.keys()
    if missing:
        print(f"  FAIL: usage block missing keys: {missing}")
        passed = False

    creation1 = usage1.get("cache_creation_input_tokens", 0)
    read1 = usage1.get("cache_read_input_tokens", 0)

    if creation1 > 0:
        print(f"  ✓ cache_creation_input_tokens = {creation1} (cache written)")
    else:
        print(
            "  FAIL: cache_creation_input_tokens == 0 — cache was NOT written. "
            "Check that the system prompt exceeds the 2048-token minimum and that "
            "the top-level cache_control field is present in the payload."
        )
        passed = False

    if read1 == 0:
        print("  ✓ cache_read_input_tokens = 0 (no prior cache — expected)")
    else:
        print(
            f"  WARN: cache_read_input_tokens = {read1} on first request (stale cache?)"
        )

    # ------------------------------------------------------------------
    # Wait before second request
    # ------------------------------------------------------------------
    print(f"\nWaiting {INTER_REQUEST_WAIT_SECONDS}s for cache availability...")
    time.sleep(INTER_REQUEST_WAIT_SECONDS)

    # ------------------------------------------------------------------
    # Request 2 — expect cache READ
    # ------------------------------------------------------------------
    print("Request 2 (expect cache READ):")
    try:
        resp2 = send_request(api_key, payload)
    except requests.HTTPError as exc:
        print(f"  ERROR: HTTP {exc.response.status_code} — {exc.response.text}")
        return False

    usage2 = resp2.get("usage", {})
    print(f"  usage: {json.dumps(usage2)}")

    creation2 = usage2.get("cache_creation_input_tokens", 0)
    read2 = usage2.get("cache_read_input_tokens", 0)

    if read2 > 0:
        print(f"  ✓ cache_read_input_tokens = {read2} (cache hit!)")
    else:
        print(
            "  FAIL: cache_read_input_tokens == 0 — cache was NOT read. "
            "The payload may have changed between requests, invalidating the hash. "
            "Ensure generate_padding_system_prompt() returns an identical string "
            "on every call and that no per-request fields (e.g. timestamps) differ."
        )
        passed = False

    if creation2 == 0:
        print("  ✓ cache_creation_input_tokens = 0 (no new write — expected)")
    else:
        print(
            f"  WARN: cache_creation_input_tokens = {creation2} on second request (re-wrote cache?)"
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    if passed:
        print(f"\nCACHE WORKING: write={creation1} tokens, read={read2} tokens")
    else:
        print("\nCACHE NOT WORKING — see FAIL messages above for diagnostics")

    return passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY not set. Add it to .env or export it as an environment variable."
        )
        sys.exit(1)

    passed = test_cache_write_then_read(api_key)

    print("\n=== RESULT ===")
    print(f"  cache_write_then_read: {'PASS' if passed else 'FAIL'}")

    sys.exit(0 if passed else 1)
