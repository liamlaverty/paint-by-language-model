"""Stroke VLM Client for querying VLMs for stroke suggestions."""

import json
import logging
import re
from datetime import datetime
from typing import Any

from config import LMSTUDIO_BASE_URL, VLM_MODEL, VLM_TIMEOUT
from lmstudio_client import LMStudioClient
from models.stroke_vlm_response import StrokeVLMResponse

logger = logging.getLogger(__name__)


class StrokeVLMClient:
    """Client for querying VLMs to suggest artistic strokes."""

    def __init__(
        self, base_url: str = LMSTUDIO_BASE_URL, model: str = VLM_MODEL, timeout: int = VLM_TIMEOUT
    ):
        """
        Initialize Stroke VLM Client.

        Args:
            base_url (str): LMStudio server URL
            model (str): VLM model identifier
            timeout (int): Request timeout in seconds
        """
        self.lmstudio_client = LMStudioClient(base_url=base_url, model=model, timeout=timeout)
        self.model = model
        self.timeout = timeout

        # Storage for interaction history (for debugging and tracing)
        self.interaction_history: list[dict[str, Any]] = []
        self.last_raw_response: str | None = None
        self.last_parsed_response: StrokeVLMResponse | None = None

        logger.info(f"Initialized StrokeVLMClient with model: {model}")

    def suggest_stroke(
        self,
        canvas_image: bytes,
        artist_name: str,
        subject: str,
        iteration: int,
        strategy_context: str = "",
    ) -> StrokeVLMResponse:
        """
        Query VLM for next stroke suggestion.

        Args:
            canvas_image (bytes): Current canvas as image bytes
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number
            strategy_context (str): Recent strategic context

        Returns:
            StrokeVLMResponse: Stroke and optional strategy update

        Raises:
            ConnectionError: If VLM server unreachable
            ValueError: If response cannot be parsed
            RuntimeError: For other VLM errors
        """
        logger.info(f"Requesting stroke suggestion for iteration {iteration}")

        # Build prompt
        prompt = self._build_stroke_prompt(
            artist_name=artist_name,
            subject=subject,
            iteration=iteration,
            strategy_context=strategy_context,
        )

        # Query VLM
        try:
            response_text = self.lmstudio_client.query_multimodal(
                prompt=prompt, image_bytes=canvas_image
            )

            # Parse response
            stroke_response = self._parse_stroke_response(response_text)

            # Store raw and parsed responses
            self.last_raw_response = response_text
            self.last_parsed_response = stroke_response

            # Store in interaction history
            self._record_interaction(
                iteration=iteration,
                artist_name=artist_name,
                subject=subject,
                prompt=prompt,
                raw_response=response_text,
                parsed_response=stroke_response,
            )

            logger.info(f"Received stroke suggestion: {stroke_response['stroke']['reasoning']}")
            return stroke_response

        except ConnectionError:
            logger.error("Failed to connect to VLM server")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse VLM response as JSON: {e}")
            logger.debug(f"Raw response: {response_text}")
            raise ValueError(f"VLM returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during VLM query: {e}")
            raise RuntimeError(f"VLM query failed: {e}") from e

    def _build_stroke_prompt(
        self, artist_name: str, subject: str, iteration: int, strategy_context: str
    ) -> str:
        """
        Build prompt for stroke suggestion.

        Args:
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number
            strategy_context (str): Recent strategic context

        Returns:
            str: Formatted prompt
        """
        strategy_section = ""
        if strategy_context:
            strategy_section = f"\n\nRecent Strategy Context:\n{strategy_context}"

        prompt = f"""You are an expert art director specializing in {artist_name}'s artistic style.

Current Canvas: [Image attached]
Subject: {subject}
Iteration: {iteration}{strategy_section}

Task: Suggest ONE single stroke (straight line) to add to this canvas to make it more evocative of {artist_name}'s style.

Consider:
- {artist_name}'s characteristic brushwork, color palette, and composition
- The current state of the canvas
- Building towards a complete composition
- Creating new original work, not copying existing pieces

Respond in JSON format:
{{
  "stroke": {{
    "type": "line",
    "start_x": <int>,
    "start_y": <int>,
    "end_x": <int>,
    "end_y": <int>,
    "color_hex": "#RRGGBB",
    "thickness": <int 1-10>,
    "opacity": <float 0.0-1.0>,
    "reasoning": "<brief explanation>"
  }},
  "updated_strategy": "<optional: updated strategy for next iterations or null>"
}}

IMPORTANT: Respond ONLY with valid JSON. Do not include any text before or after the JSON object."""

        return prompt

    def _parse_stroke_response(self, response_text: str) -> StrokeVLMResponse:
        """
        Parse VLM response into StrokeVLMResponse.

        Args:
            response_text (str): Raw VLM response

        Returns:
            StrokeVLMResponse: Parsed stroke response

        Raises:
            ValueError: If JSON invalid or missing fields
            json.JSONDecodeError: If not valid JSON
        """
        # Try to extract JSON if VLM included extra text
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        json_text = json_match.group(0) if json_match else response_text

        # Remove JSON comments (VLMs sometimes add these)
        # Remove single-line comments: // comment
        json_text = re.sub(r"//.*?(?=\n|$)", "", json_text)
        # Remove multi-line comments: /* comment */
        json_text = re.sub(r"/\*.*?\*/", "", json_text, flags=re.DOTALL)

        # Fix multi-line strings within JSON values (replace newlines within quotes with spaces)
        # This handles cases where VLMs put actual newlines in string values
        def fix_multiline_strings(match: re.Match[str]) -> str:
            """Replace newlines within quoted strings with spaces."""
            value = match.group(0)
            return value.replace("\n", " ").replace("\r", " ")

        # Match quoted strings and fix newlines within them
        json_text = re.sub(r'"[^"]*"', fix_multiline_strings, json_text, flags=re.DOTALL)

        # Parse JSON
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.error(f"Attempted to parse: {json_text[:500]}")
            raise

        # Validate structure
        if "stroke" not in data:
            raise ValueError("Response missing 'stroke' field")

        stroke = data["stroke"]
        required_fields = [
            "type",
            "start_x",
            "start_y",
            "end_x",
            "end_y",
            "color_hex",
            "thickness",
            "opacity",
            "reasoning",
        ]

        for field in required_fields:
            if field not in stroke:
                raise ValueError(f"Stroke missing required field: {field}")

        # Build response
        response: StrokeVLMResponse = {
            "stroke": {
                "type": stroke["type"],
                "start_x": int(stroke["start_x"]),
                "start_y": int(stroke["start_y"]),
                "end_x": int(stroke["end_x"]) if stroke["end_x"] is not None else None,
                "end_y": int(stroke["end_y"]) if stroke["end_y"] is not None else None,
                "color_hex": str(stroke["color_hex"]),
                "thickness": int(stroke["thickness"]),
                "opacity": float(stroke["opacity"]),
                "reasoning": str(stroke["reasoning"]),
            },
            "updated_strategy": data.get("updated_strategy"),
        }

        return response

    def _record_interaction(
        self,
        iteration: int,
        artist_name: str,
        subject: str,
        prompt: str,
        raw_response: str,
        parsed_response: StrokeVLMResponse,
    ) -> None:
        """
        Record an interaction in the history for tracing and debugging.

        Args:
            iteration (int): Iteration number
            artist_name (str): Target artist name
            subject (str): Subject being painted
            prompt (str): The prompt sent to the VLM
            raw_response (str): Raw VLM response text
            parsed_response (StrokeVLMResponse): Parsed stroke response
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
            "artist_name": artist_name,
            "subject": subject,
            "prompt": prompt,
            "raw_response": raw_response,
            "parsed_response": parsed_response,
            "model": self.model,
        }
        self.interaction_history.append(interaction)
        logger.debug(f"Recorded interaction for iteration {iteration}")

    def get_interaction_history(self) -> list[dict[str, Any]]:
        """
        Get the full interaction history.

        Returns:
            list[dict[str, Any]]: List of all recorded interactions
        """
        return self.interaction_history

    def clear_history(self) -> None:
        """
        Clear the interaction history.

        Useful when starting a new generation session.
        """
        self.interaction_history.clear()
        self.last_raw_response = None
        self.last_parsed_response = None
        logger.info("Cleared interaction history")
