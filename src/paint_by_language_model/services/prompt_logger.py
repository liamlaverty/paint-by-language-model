"""PromptLogger utility for persisting full LLM prompt/response pairs to disk."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class PromptLogger:
    """Persists full prompt/response pairs for every LLM interaction."""

    def __init__(self, artwork_dir: Path) -> None:
        """
        Initialize PromptLogger.

        Args:
            artwork_dir (Path): Root output directory for the artwork
                                (e.g. src/output/<artwork-id>/)
        """
        self.log_dir = artwork_dir / "prompt-log"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"PromptLogger initialised. Log directory: {self.log_dir}")

    def _generate_filename(self, prompt_type: str) -> str:
        """
        Generate a filesystem-safe filename for a prompt log entry.

        Uses ISO-8601 datetime with microseconds to avoid collisions when
        multiple calls happen within the same second.
        Format: ``YYYY-MM-DDTHH-MM-SS-<microseconds>-<type>.json``

        Args:
            prompt_type (str): Interaction type (``"plan"``, ``"stroke"``,
                               ``"evaluation"``)

        Returns:
            str: Filename string (not a full path)
        """
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%dT%H-%M-%S")
        microseconds = f"{now.microsecond:06d}"
        return f"{date_str}-{microseconds}-{prompt_type}.json"

    def log_interaction(
        self,
        prompt_type: str,
        prompt: str,
        raw_response: str,
        model: str,
        provider: str,
        temperature: float,
        images: list[dict[str, Any]] | None = None,
        context: dict[str, Any] | None = None,
    ) -> Path:
        """
        Write a prompt/response pair to disk as a JSON file.

        Args:
            prompt_type (str): Interaction type (``"plan"``, ``"stroke"``,
                               ``"evaluation"``)
            prompt (str): Full prompt text sent to the LLM
            raw_response (str): Full raw response text from the LLM
            model (str): Model identifier (e.g. ``"claude-sonnet-4-6"``)
            provider (str): Provider name (e.g. ``"anthropic"``,
                            ``"mistral"``, ``"lmstudio"``)
            temperature (float): Temperature used for the request
            images (list[dict[str, Any]] | None): Image metadata list.
                Each dict contains ``"label"`` (str) and ``"size_bytes"``
                (int) keys. Set to ``None`` for text-only interactions.
            context (dict[str, Any] | None): Type-specific metadata dict.
                Set to ``None`` when no extra context is available.

        Returns:
            Path: Path to the saved log file
        """
        payload: dict[str, Any] = {
            "type": prompt_type,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "provider": provider,
            "temperature": temperature,
            "prompt": prompt,
            "raw_response": raw_response,
            "images": images,
            "context": context,
        }

        filename = self._generate_filename(prompt_type)
        file_path = self.log_dir / filename

        with open(file_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2, ensure_ascii=False)

        logger.debug(f"Saved prompt log: {filename}")
        return file_path
