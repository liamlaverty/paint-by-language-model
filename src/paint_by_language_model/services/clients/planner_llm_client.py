"""Planner LLM Client for generating painting plans."""

import json
import logging
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from config import (
    API_BASE_URL,
    API_KEY,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    COLOR_HEX_PATTERN,
    DEFAULT_STROKES_PER_QUERY,
    MIN_STROKES_PER_LAYER,
    OUTPUT_DIR,
    PLANNER_MAX_TOKENS,
    PLANNER_MODEL,
    PLANNER_PROMPT_TEMPERATURE,
    PLANNER_TIMEOUT,
    SUPPORTED_STROKE_TYPES,
)
from models.painting_plan import PaintingPlan, PlanLayer
from services.prompt_logger import PromptLogger
from utils.json_utils import clean_and_parse_json
from vlm_client import VLMClient

logger = logging.getLogger(__name__)


class PlannerLLMClient:
    """Client for querying LLMs to generate painting plans."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        model: str = PLANNER_MODEL,
        timeout: int = PLANNER_TIMEOUT,
        api_key: str = API_KEY,
        temperature: float = PLANNER_PROMPT_TEMPERATURE,
        prompt_logger: PromptLogger | None = None,
        min_strokes_per_layer: int = MIN_STROKES_PER_LAYER,
    ) -> None:
        """
        Initialize Planner LLM Client.

        Args:
            base_url (str): LLM API server URL
            model (str): LLM model identifier
            timeout (int): Request timeout in seconds
            api_key (str): API key for authentication
            temperature (float): Sampling temperature for plan generation
            prompt_logger (PromptLogger | None): Optional logger for persisting
                full prompt/response pairs to disk
            min_strokes_per_layer (int): Minimum iterations on a layer before
                ``layer_complete: true`` is honoured. Defaults to the config value.
                Evaluated once at class-definition time; the caller must pass
                an explicit value if a runtime override is required.
        """
        self.client = VLMClient(
            base_url=base_url,
            model=model,
            timeout=timeout,
            api_key=api_key,
            temperature=temperature,
        )
        self.model = model
        self.timeout = timeout
        self.prompt_logger = prompt_logger
        self.min_strokes_per_layer = min_strokes_per_layer

        # Storage for interaction history (for debugging and tracing)
        self.interaction_history: list[dict[str, Any]] = []
        self.last_raw_response: str | None = None
        self.last_parsed_response: PaintingPlan | None = None

        logger.info(f"Initialized PlannerLLMClient with model: {model}")

    def _log_parsing_exception(
        self,
        artist_name: str,
        subject: str,
        raw_response: str,
        exception: Exception,
        prompt: str = "",
    ) -> Path:
        """
        Log parsing exception with raw LLM response for debugging.

        Args:
            artist_name (str): Artist name from the request
            subject (str): Subject from the request
            raw_response (str): Raw LLM response that failed to parse
            exception (Exception): The exception that was raised
            prompt (str): The prompt sent to the LLM

        Returns:
            Path: Path to the saved log file
        """
        # Create exception log directory
        exception_log_dir = OUTPUT_DIR / "exception_logs" / "planner"
        exception_log_dir.mkdir(parents=True, exist_ok=True)

        # Generate log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_subject = "".join(c if c.isalnum() else "_" for c in subject[:30])
        log_filename = f"planner_{artist_name}_{safe_subject}_{timestamp}.log"
        log_filepath = exception_log_dir / log_filename

        # Write exception details
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write("Planner LLM Parsing Exception\n")
            f.write("=" * 80 + "\n\n")
            f.write(f"Artist: {artist_name}\n")
            f.write(f"Subject: {subject}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Exception: {type(exception).__name__}\n")
            f.write(f"Message: {str(exception)}\n\n")

            if prompt:
                f.write("Prompt Sent to LLM:\n")
                f.write("-" * 80 + "\n")
                f.write(prompt)
                f.write("\n" + "-" * 80 + "\n\n")

            f.write("Raw LLM Response:\n")
            f.write("-" * 80 + "\n")
            f.write(raw_response)
            f.write("\n" + "-" * 80 + "\n\n")

            f.write("Traceback:\n")
            f.write("-" * 80 + "\n")
            f.write(traceback.format_exc())
            f.write("-" * 80 + "\n")

        logger.error(f"Parsing exception logged to: {log_filepath}")
        return log_filepath

    def generate_plan(
        self,
        artist_name: str,
        subject: str,
        expanded_subject: str | None,
        stroke_types: list[str],
    ) -> PaintingPlan:
        """
        Generate a painting plan for the given artist and subject.

        Args:
            artist_name (str): Target artist whose style to emulate
            subject (str): Brief subject description
            expanded_subject (str | None): Detailed description of final image
            stroke_types (list[str]): Available stroke types for the painting

        Returns:
            PaintingPlan: Complete painting plan with ordered layers

        Raises:
            ConnectionError: If LLM server unreachable
            ValueError: If response cannot be parsed or is invalid
            RuntimeError: For other LLM errors
        """
        logger.info(f"Generating painting plan for '{subject}' in style of {artist_name}")

        # Build prompt
        prompt = self._build_planning_prompt(
            artist_name=artist_name,
            subject=subject,
            expanded_subject=expanded_subject,
            stroke_types=stroke_types,
        )

        # Query LLM (text-only, no image) with sufficient max_tokens for detailed plans
        try:
            response_text = self.client.query(
                prompt=prompt, max_tokens=PLANNER_MAX_TOKENS, system_prompt=""
            )

            # Store raw response immediately so it is available even if parsing fails
            self.last_raw_response = response_text

            # Parse response
            painting_plan = self._parse_plan_response(
                response_text, allowed_stroke_types=stroke_types
            )

            # Store parsed response
            self.last_parsed_response = painting_plan

            # Record interaction in history
            self._record_interaction(
                artist_name=artist_name,
                subject=subject,
                prompt=prompt,
                raw_response=response_text,
                parsed_response=painting_plan,
                layer_count=painting_plan["total_layers"],
            )

            if self.prompt_logger:
                self.prompt_logger.log_interaction(
                    prompt_type="plan",
                    prompt=prompt,
                    raw_response=response_text,
                    model=self.model,
                    provider=self.client.provider,
                    temperature=self.client.temperature,
                    images=None,
                    context={
                        "artist_name": artist_name,
                        "subject": subject,
                        "layer_count": painting_plan["total_layers"],
                    },
                )

            logger.info(
                f"Generated painting plan with {painting_plan['total_layers']} layers: "
                f"{[layer['name'] for layer in painting_plan['layers']]}"
            )
            return painting_plan

        except ConnectionError:
            logger.error("Failed to connect to LLM server")
            raise
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Save raw response for debugging
            if "response_text" in locals() and response_text:
                log_path = self._log_parsing_exception(
                    artist_name=artist_name,
                    subject=subject,
                    raw_response=response_text,
                    exception=e,
                    prompt=prompt if "prompt" in locals() else "",
                )
                logger.error(f"Raw LLM response saved to: {log_path}")
            raise ValueError(f"LLM returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during LLM query: {e}")
            if "response_text" in locals() and response_text:
                self._log_parsing_exception(
                    artist_name=artist_name,
                    subject=subject,
                    raw_response=response_text,
                    exception=e,
                    prompt=prompt if "prompt" in locals() else "",
                )
            raise RuntimeError(f"LLM query failed: {e}") from e

    def _build_planning_prompt(
        self,
        artist_name: str,
        subject: str,
        expanded_subject: str | None,
        stroke_types: list[str],
    ) -> str:
        """
        Build prompt for painting plan generation.

        Args:
            artist_name (str): Target artist whose style to emulate
            subject (str): Brief subject description
            expanded_subject (str | None): Detailed description of final image
            stroke_types (list[str]): Available stroke types for the painting

        Returns:
            str: Formatted prompt
        """
        expanded_section = f"\nExpanded description: {expanded_subject}" if expanded_subject else ""

        prompt = f"""You are an expert art director planning a painting in the style of {artist_name}.

Subject: {subject}{expanded_section}

Available stroke types: {", ".join(stroke_types)}
Canvas dimensions: {CANVAS_WIDTH}x{CANVAS_HEIGHT} pixels
Minimum iterations per layer: {self.min_strokes_per_layer} (each iteration applies up to
{DEFAULT_STROKES_PER_QUERY} strokes, so each layer will contain at most
{self.min_strokes_per_layer * DEFAULT_STROKES_PER_QUERY} individual strokes before it can be
marked complete)

Task: Create a step-by-step layer plan for painting this image. Each layer will be
executed sequentially — the painter can only ADD onto the canvas, not remove or switch
between layers. Earlier layers will be painted over by later ones.

Plan for 4-8 layers total. Fewer, well-defined layers work better than many small ones.
Common layer sequence: background → mid-ground → main subjects → details/highlights.

For each layer, specify:
- name: A short descriptive name (e.g. "Sky background", "Main figure")
- description: What should be drawn in this layer and where on the canvas
- colour_palette: A list of hex colour codes appropriate for this layer (limit to 10, prefer fewer)
- stroke_types: Which of the available stroke types are best suited
- techniques: Artistic techniques to apply (e.g. "broad sweeping strokes", "stippling")
- shapes: Typical shapes and forms (e.g. "horizontal bands", "organic curves")
- highlights: Guidance on emphasis, lighting, and texture in this layer

Consider {artist_name}'s characteristic:
- Colour choices and palette
- Brushwork and mark-making style
- Compositional approach
- Treatment of light and shadow
- Overall mood and atmosphere

RESPONSE FORMAT (JSON only):
{{
  "artist_name": "{artist_name}",
  "subject": "{subject}",
  "expanded_subject": {json.dumps(expanded_subject)},
  "total_layers": <int>,
  "layers": [
    {{
      "layer_number": 1,
      "name": "...",
      "description": "...",
      "colour_palette": ["#XXXXXX", ...],
      "stroke_types": ["line", "arc", ...],
      "techniques": "...",
      "shapes": "...",
      "highlights": "..."
    }}
    // ... more layers
  ],
  "overall_notes": "..."
}}

IMPORTANT: Respond ONLY with valid JSON. Do not include markdown formatting."""

        return prompt

    def _parse_plan_response(
        self, response_text: str, allowed_stroke_types: list[str] | None = None
    ) -> PaintingPlan:
        """
        Parse LLM response into PaintingPlan.

        Args:
            response_text (str): Raw LLM response
            allowed_stroke_types (list[str] | None): Active allowed stroke types used to
                validate and filter each layer's ``stroke_types`` list.  Types that are
                in ``SUPPORTED_STROKE_TYPES`` but not in ``allowed_stroke_types`` are
                silently removed with a warning rather than raising.  Types that are not
                in ``SUPPORTED_STROKE_TYPES`` at all (genuinely unknown) still raise a
                ``ValueError``.  Defaults to ``None`` which treats all supported types as
                allowed.

        Returns:
            PaintingPlan: Parsed painting plan

        Raises:
            ValueError: If JSON invalid, missing fields, or validation fails
            json.JSONDecodeError: If not valid JSON
        """
        # Use shared robust JSON parsing utility
        data = clean_and_parse_json(response_text)

        # Validate top-level structure
        if "layers" not in data:
            raise ValueError("Response missing 'layers' field")

        if not isinstance(data["layers"], list):
            raise ValueError("'layers' field must be a list")

        if len(data["layers"]) == 0:
            raise ValueError("'layers' list cannot be empty")

        # Validate each layer
        validated_layers: list[PlanLayer] = []
        for idx, layer in enumerate(data["layers"]):
            if not isinstance(layer, dict):
                raise ValueError(f"Layer {idx} is not a dictionary")

            # Check required fields
            required_fields = [
                "layer_number",
                "name",
                "description",
                "colour_palette",
                "stroke_types",
                "techniques",
                "shapes",
                "highlights",
            ]
            missing_fields = [field for field in required_fields if field not in layer]
            if missing_fields:
                raise ValueError(
                    f"Layer {idx} missing required fields: {', '.join(missing_fields)}"
                )

            # Validate layer_number is sequential
            expected_layer_num = idx + 1
            actual_layer_num = layer["layer_number"]
            if actual_layer_num != expected_layer_num:
                raise ValueError(
                    f"Layer {idx} has layer_number {actual_layer_num}, expected {expected_layer_num}"
                )

            # Validate colour_palette
            if not isinstance(layer["colour_palette"], list):
                raise ValueError(f"Layer {idx} colour_palette must be a list")

            for color in layer["colour_palette"]:
                if not isinstance(color, str):
                    raise ValueError(f"Layer {idx} has non-string color: {color}")
                if not re.match(COLOR_HEX_PATTERN, color):
                    raise ValueError(
                        f"Layer {idx} has invalid hex color: {color} (expected format: #RRGGBB)"
                    )

            # Validate stroke_types
            if not isinstance(layer["stroke_types"], list):
                raise ValueError(f"Layer {idx} stroke_types must be a list")

            effective_allowed = allowed_stroke_types or SUPPORTED_STROKE_TYPES
            filtered_stroke_types: list[str] = []
            for stroke_type in layer["stroke_types"]:
                if stroke_type not in SUPPORTED_STROKE_TYPES:
                    raise ValueError(
                        f"Layer {idx} has unsupported stroke type: {stroke_type} "
                        f"(supported: {', '.join(SUPPORTED_STROKE_TYPES)})"
                    )
                if stroke_type not in effective_allowed:
                    logger.warning(
                        f"Layer {idx} requested stroke type '{stroke_type}' which is not in the "
                        f"allowed list {effective_allowed}; removing from layer stroke_types"
                    )
                else:
                    filtered_stroke_types.append(stroke_type)

            if not filtered_stroke_types:
                logger.warning(
                    f"Layer {idx} had no valid stroke types after filtering; "
                    f"falling back to all allowed types: {effective_allowed}"
                )
                filtered_stroke_types = list(effective_allowed)

            layer["stroke_types"] = filtered_stroke_types

            # Build validated layer
            validated_layer: PlanLayer = {
                "layer_number": int(layer["layer_number"]),
                "name": str(layer["name"]),
                "description": str(layer["description"]),
                "colour_palette": layer["colour_palette"],
                "stroke_types": layer["stroke_types"],
                "techniques": str(layer["techniques"]),
                "shapes": str(layer["shapes"]),
                "highlights": str(layer["highlights"]),
            }
            validated_layers.append(validated_layer)

        # Validate total_layers matches actual layer count
        total_layers = data.get("total_layers", len(validated_layers))
        if total_layers != len(validated_layers):
            raise ValueError(
                f"total_layers ({total_layers}) does not match actual layer count "
                f"({len(validated_layers)})"
            )

        # Build final PaintingPlan
        painting_plan: PaintingPlan = {
            "artist_name": str(data.get("artist_name", "")),
            "subject": str(data.get("subject", "")),
            "expanded_subject": (
                str(data["expanded_subject"]) if data.get("expanded_subject") else None
            ),
            "total_layers": total_layers,
            "layers": validated_layers,
            "overall_notes": str(data.get("overall_notes", "")),
        }

        return painting_plan

    def _record_interaction(
        self,
        artist_name: str,
        subject: str,
        prompt: str,
        raw_response: str,
        parsed_response: PaintingPlan,
        layer_count: int,
    ) -> None:
        """
        Record an interaction in the history for tracing and debugging.

        Args:
            artist_name (str): Target artist name
            subject (str): Subject being painted
            prompt (str): The prompt sent to the LLM
            raw_response (str): Raw LLM response text
            parsed_response (PaintingPlan): Parsed painting plan
            layer_count (int): Number of layers in the plan
        """
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "artist_name": artist_name,
            "subject": subject,
            "prompt": prompt,
            "raw_response": raw_response,
            "parsed_response": parsed_response,
            "model": self.model,
            "layer_count": layer_count,
        }
        self.interaction_history.append(interaction)
        logger.debug(f"Recorded interaction for {artist_name} - {subject}: {layer_count} layers")

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

        Useful when starting a new planning session.
        """
        self.interaction_history.clear()
        self.last_raw_response = None
        self.last_parsed_response = None
        logger.info("Cleared interaction history")
