"""Manual integration test for Anthropic prompt caching.

Verifies that prompt caching works correctly by inspecting the ``usage`` fields
in the API response. Sends two identical requests via the production
``VLMClient`` and asserts that the first writes to cache
(cache_creation_input_tokens > 0) and the second reads from cache
(cache_read_input_tokens > 0).

Usage:
    conda activate paint-by-language-model
    python tests/manual_test_anthropic_caching.py

Prerequisites:
    - Set ANTHROPIC_API_KEY in your .env file or as an environment variable.
    - Ensure the paint-by-language-model conda environment is active.

Notes:
    - Uses the model configured via ``config.ANTHROPIC_VLM_MODEL``.
    - Requires a system prompt >= 4096 tokens (Haiku 4.5) or >= 2048 tokens
      (Haiku 3) to meet the model's caching minimum. Below this threshold
      caching is silently skipped with no error returned.
    - The 5-minute cache TTL means the second request must arrive within 5
      minutes of the first for a cache hit to register.
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

import config
from dotenv import load_dotenv
from vlm_client import VLMClient

load_dotenv(Path(__file__).parent.parent / ".env")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_MESSAGE = "mary had a little"

# How long to wait between Request 1 and Request 2 (seconds).
# The cache is available as soon as the first response begins, but a small
# pause avoids any edge-case race conditions.
INTER_REQUEST_WAIT_SECONDS = 2


# ---------------------------------------------------------------------------
# System prompt generator
# ---------------------------------------------------------------------------

# A single block of art-analysis instructional text (~150 words / ~200 tokens).
# Repeated enough times to exceed the 4096-token minimum for Claude Haiku 4.5.
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
        str: Static instructional text of approximately 5600 tokens.
    """
    return _INSTRUCTION_BLOCK * _REPEAT_COUNT


def _make_anthropic_client() -> VLMClient:
    """
    Build a VLMClient configured for the Anthropic provider.

    Forces ``provider="anthropic"`` regardless of the ``PROVIDER`` value in
    ``.env`` so the caching test always targets the Anthropic Messages API.

    Returns:
        VLMClient: Client pointing at the Anthropic Messages API.
    """
    return VLMClient(
        provider="anthropic",
        base_url=config.ANTHROPIC_BASE_URL,
        model=config.ANTHROPIC_VLM_MODEL,
        api_key=config.ANTHROPIC_API_KEY,
    )


# ---------------------------------------------------------------------------
# Test function
# ---------------------------------------------------------------------------


def test_cache_write_then_read(api_key: str) -> bool:
    """
    Prove Anthropic prompt caching works end-to-end via ``VLMClient``.

    Sends two identical requests through the production ``VLMClient.query``
    path. Asserts that the first request writes content to the cache
    (cache_creation_input_tokens > 0) and the second request reads that
    content from the cache (cache_read_input_tokens > 0).

    The ``usage`` block is retrieved via ``VLMClient.last_usage`` which is
    populated after each successful API call.

    Args:
        api_key (str): Anthropic API key (validated by the caller; not used
            directly here — the client reads from ``config.ANTHROPIC_API_KEY``).

    Returns:
        bool: True if both assertions pass, False otherwise.
    """
    print("\n=== Test: cache_write_then_read ===")

    padding = generate_padding_system_prompt()
    estimated_words = len(padding.split())
    # Rough token estimate: English averages ~0.75 words per token
    estimated_tokens = int(estimated_words / 0.75)
    print(f"System prompt length: ~{estimated_tokens} tokens ({estimated_words} words)")

    client = _make_anthropic_client()
    print(f"Model: {client.model}")
    print(f'System prompt preview: "{padding[:100]}..."')

    passed = True

    # ------------------------------------------------------------------
    # Request 1 — expect cache WRITE
    # ------------------------------------------------------------------
    print("\nRequest 1 (expect cache WRITE):")
    try:
        client.query(prompt=USER_MESSAGE, max_tokens=50, system_prompt=padding)
    except Exception as exc:
        print(f"  ERROR: {exc}")
        return False

    usage1: dict = client.last_usage or {}
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
            "Check that the system prompt exceeds the model's minimum token threshold "
            "and that block-level cache_control is present in the payload."
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
        client.query(prompt=USER_MESSAGE, max_tokens=50, system_prompt=padding)
    except Exception as exc:
        print(f"  ERROR: {exc}")
        return False

    usage2: dict = client.last_usage or {}
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
