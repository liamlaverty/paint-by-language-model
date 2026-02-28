"""Stroke VLM Client for querying VLMs for stroke suggestions."""

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from models import PaintingPlan, PlanLayer

from config import (
    API_BASE_URL,
    API_KEY,
    CANVAS_HEIGHT,
    CANVAS_WIDTH,
    DEFAULT_STROKES_PER_QUERY,
    MAX_STROKE_OPACITY,
    MAX_STROKE_THICKNESS,
    MAX_STROKES_PER_QUERY,
    MIN_STROKE_OPACITY,
    MIN_STROKE_THICKNESS,
    MIN_STROKES_PER_QUERY,
    STROKE_PROMPT_TEMPERATURE,
    VLM_MODEL,
    VLM_TIMEOUT,
)
from models.stroke import Stroke
from models.stroke_vlm_response import StrokeVLMResponse
from services.prompt_logger import PromptLogger
from services.stroke_sample_generator import StrokeSampleGenerator
from utils.json_utils import clean_and_parse_json
from vlm_client import VLMClient

logger = logging.getLogger(__name__)


class StrokeVLMClient:
    """Client for querying VLMs to suggest artistic strokes."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        model: str = VLM_MODEL,
        timeout: int = VLM_TIMEOUT,
        api_key: str = API_KEY,
        temperature: float = STROKE_PROMPT_TEMPERATURE,
        prompt_logger: PromptLogger | None = None,
    ):
        """
        Initialize Stroke VLM Client.

        Args:
            base_url (str): VLM API server URL
            model (str): VLM model identifier
            timeout (int): Request timeout in seconds
            api_key (str): API key for authentication
            temperature (float): Sampling temperature for stroke generation
            prompt_logger (PromptLogger | None): Optional logger for persisting
                full prompt/response pairs to disk
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

        # Storage for interaction history (for debugging and tracing)
        self.interaction_history: list[dict[str, Any]] = []
        self.last_raw_response: str | None = None
        self.last_parsed_response: StrokeVLMResponse | None = None

        logger.info(f"Initialized StrokeVLMClient with model: {model}")

        self.sample_generator = StrokeSampleGenerator()
        self._stroke_samples = self.sample_generator.generate_all_samples()
        logger.info(f"Generated {len(self._stroke_samples)} stroke sample images")

    def suggest_strokes(
        self,
        canvas_image: bytes,
        artist_name: str,
        subject: str,
        iteration: int,
        strategy_context: str = "",
        num_strokes: int = DEFAULT_STROKES_PER_QUERY,
        painting_plan: "PaintingPlan | None" = None,
        current_layer: "PlanLayer | None" = None,
        expanded_subject: str | None = None,
    ) -> StrokeVLMResponse:
        """
        Query VLM for multiple stroke suggestions.

        Args:
            canvas_image (bytes): Current canvas as image bytes
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number
            strategy_context (str): Recent strategic context
            num_strokes (int): Number of strokes to request (default: 5)
            painting_plan (PaintingPlan | None): Complete painting plan
            current_layer (PlanLayer | None): Current layer information
            expanded_subject (str | None): Detailed subject description

        Returns:
            StrokeVLMResponse: List of strokes and optional strategy update

        Raises:
            ConnectionError: If VLM server unreachable
            ValueError: If response cannot be parsed
            RuntimeError: For other VLM errors
        """
        # Validate and clamp num_strokes
        if num_strokes < MIN_STROKES_PER_QUERY:
            logger.warning(
                f"num_strokes {num_strokes} below minimum, clamping to {MIN_STROKES_PER_QUERY}"
            )
            num_strokes = MIN_STROKES_PER_QUERY
        elif num_strokes > MAX_STROKES_PER_QUERY:
            logger.warning(
                f"num_strokes {num_strokes} above maximum, clamping to {MAX_STROKES_PER_QUERY}"
            )
            num_strokes = MAX_STROKES_PER_QUERY

        logger.info(f"Requesting {num_strokes} stroke suggestions for iteration {iteration}")

        # Build prompt
        prompt = self._build_stroke_prompt(
            artist_name=artist_name,
            subject=subject,
            iteration=iteration,
            strategy_context=strategy_context,
            num_strokes=num_strokes,
            painting_plan=painting_plan,
            current_layer=current_layer,
            expanded_subject=expanded_subject,
        )

        # Query VLM
        try:
            images: list[tuple[bytes, str]] = [
                (canvas_image, "Current canvas"),
            ]
            for stroke_type, sample_bytes in self._stroke_samples.items():
                images.append((sample_bytes, f"{stroke_type.upper()} stroke sample"))

            response_text = self.client.query_multimodal_multi_image(
                prompt=prompt,
                images=images,
            )

            # Store raw response immediately so it is always available,
            # even if parsing fails below.
            self.last_raw_response = response_text

            # Parse response
            stroke_response = self._parse_stroke_response(response_text)

            # Store parsed response
            self.last_parsed_response = stroke_response

            # Store in interaction history
            self._record_interaction(
                iteration=iteration,
                artist_name=artist_name,
                subject=subject,
                prompt=prompt,
                raw_response=response_text,
                parsed_response=stroke_response,
                num_strokes_requested=num_strokes,
                num_strokes_parsed=len(stroke_response["strokes"]),
            )

            if self.prompt_logger:
                image_metadata: list[dict[str, Any]] = [
                    {"label": "Current canvas", "size_bytes": len(canvas_image)}
                ]
                for stroke_type, sample_bytes in self._stroke_samples.items():
                    image_metadata.append(
                        {
                            "label": f"{stroke_type.upper()} stroke sample",
                            "size_bytes": len(sample_bytes),
                        }
                    )
                self.prompt_logger.log_interaction(
                    prompt_type="stroke",
                    prompt=prompt,
                    raw_response=response_text,
                    model=self.model,
                    provider=self.client.provider,
                    temperature=self.client.temperature,
                    images=image_metadata,
                    context={
                        "iteration": iteration,
                        "artist_name": artist_name,
                        "subject": subject,
                        "num_strokes_requested": num_strokes,
                        "num_strokes_parsed": len(stroke_response["strokes"]),
                        "layer_number": current_layer["layer_number"] if current_layer else None,
                        "layer_name": current_layer["name"] if current_layer else None,
                    },
                )

            logger.info(
                f"Received {len(stroke_response['strokes'])} strokes: "
                f"{stroke_response['batch_reasoning']}"
            )
            return stroke_response

        except ConnectionError:
            logger.error("Failed to connect to VLM server")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse VLM response as JSON: {e}")
            logger.error(f"Raw response (first 500 chars): {response_text[:500]}")
            if self.prompt_logger:
                self.prompt_logger.log_interaction(
                    prompt_type="stroke",
                    prompt=prompt,
                    raw_response=response_text,
                    model=self.model,
                    provider=self.client.provider,
                    temperature=self.client.temperature,
                    context={
                        "iteration": iteration,
                        "artist_name": artist_name,
                        "subject": subject,
                        "num_strokes_requested": num_strokes,
                        "num_strokes_parsed": 0,
                        "parse_error": True,
                        "layer_number": current_layer["layer_number"] if current_layer else None,
                        "layer_name": current_layer["name"] if current_layer else None,
                    },
                )
            raise ValueError(f"VLM returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during VLM query: {e}")
            if self.last_raw_response is not None and self.prompt_logger:
                self.prompt_logger.log_interaction(
                    prompt_type="stroke",
                    prompt=prompt,
                    raw_response=self.last_raw_response,
                    model=self.model,
                    provider=self.client.provider,
                    temperature=self.client.temperature,
                    context={
                        "iteration": iteration,
                        "artist_name": artist_name,
                        "subject": subject,
                        "num_strokes_requested": num_strokes,
                        "num_strokes_parsed": 0,
                        "parse_error": True,
                        "layer_number": current_layer["layer_number"] if current_layer else None,
                        "layer_name": current_layer["name"] if current_layer else None,
                    },
                )
            raise RuntimeError(f"VLM query failed: {e}") from e

    def suggest_stroke(
        self,
        canvas_image: bytes,
        artist_name: str,
        subject: str,
        iteration: int,
        strategy_context: str = "",
    ) -> StrokeVLMResponse:
        """
        Query VLM for a single stroke suggestion.

        Convenience wrapper around suggest_strokes() for backward compatibility.

        Args:
            canvas_image (bytes): Current canvas as image bytes
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number
            strategy_context (str): Recent strategic context

        Returns:
            StrokeVLMResponse: Single stroke wrapped in list with strategy update

        Raises:
            ConnectionError: If VLM server unreachable
            ValueError: If response cannot be parsed
            RuntimeError: For other VLM errors
        """
        return self.suggest_strokes(
            canvas_image=canvas_image,
            artist_name=artist_name,
            subject=subject,
            iteration=iteration,
            strategy_context=strategy_context,
            num_strokes=1,
        )

    def _build_stroke_prompt(
        self,
        artist_name: str,
        subject: str,
        iteration: int,
        strategy_context: str,
        num_strokes: int,
        painting_plan: "PaintingPlan | None" = None,
        current_layer: "PlanLayer | None" = None,
        expanded_subject: str | None = None,
    ) -> str:
        """
        Build prompt for multiple stroke suggestions.

        Args:
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number
            strategy_context (str): Recent strategic context
            num_strokes (int): Number of strokes to request
            painting_plan (PaintingPlan | None): Complete painting plan
            current_layer (PlanLayer | None): Current layer information
            expanded_subject (str | None): Detailed subject description

        Returns:
            str: Formatted prompt
        """
        # Build subject section with optional expanded description
        subject_section = f"Subject: {subject}"
        if expanded_subject:
            subject_section += f"\nDetailed description: {expanded_subject}"

        # Build strategy context section
        strategy_section = ""
        if strategy_context:
            strategy_section = f"\n\nRecent Strategy Context:\n{strategy_context}"

        # Build painting plan section if available
        plan_section = ""
        if painting_plan and current_layer:
            import json

            plan_section = f"""

=== PAINTING PLAN ===
{json.dumps(painting_plan, indent=2)}

=== CURRENT FOCUS ===
You are currently working on Layer {current_layer["layer_number"]}: "{current_layer["name"]}"
Description: {current_layer["description"]}
Recommended colour palette: {", ".join(current_layer["colour_palette"])}
Recommended stroke types: {", ".join(current_layer["stroke_types"])}
Techniques: {current_layer["techniques"]}
Shapes: {current_layer["shapes"]}
Highlights: {current_layer["highlights"]}

Focus your strokes on this layer's objectives. Stay near the recommended palette
(don't be rigidly bound by the exact colour hex values). Stay within the
recommended techniques unless artistic judgement requires deviation.
"""
            plan_section += """

Also assess whether this layer's objectives have been sufficiently met.
If the layer goals are complete and it's time to move on, set "layer_complete" to true.
Only signal completion when the layer's description, palette, shapes, and techniques
have been adequately addressed on the canvas.
"""

        layer_complete_field = ""
        if painting_plan and current_layer:
            layer_complete_field = ',\n  "layer_complete": <boolean - true if this layer\'s objectives are sufficiently met, false otherwise>'

        prompt = f"""You are an expert artist creating a piece in the style of {artist_name}.

Current Canvas: [Image attached]
{subject_section}
Iteration: {iteration}{strategy_section}{plan_section}

Task: Suggest {num_strokes} stroke(s) to add to this canvas that evoke {artist_name}'s artistic style.

AVAILABLE STROKE TYPES:

1. LINE - Straight line between two points. See attached "LINE stroke sample" image showing 5 examples with varying thickness, colour, opacity, and angle.
   Example: {{"type": "line", "start_x": 100, "start_y": 200, "end_x": 300, "end_y": 400, "color_hex": "#FF5733", "thickness": 5, "opacity": 0.8}}
   Required fields: type, start_x, start_y, end_x, end_y, color_hex, thickness, opacity

2. ARC - Curved arc within a bounding box. See attached "ARC stroke sample" image showing 5 examples with varying bbox sizes, angle sweeps, and thickness.
   Example: {{"type": "arc", "arc_bbox": [50, 50, 250, 250], "arc_start_angle": 0, "arc_end_angle": 180, "color_hex": "#3366CC", "thickness": 3, "opacity": 0.9}}
   Required fields: type, arc_bbox (list [x0,y0,x1,y1]), arc_start_angle (degrees), arc_end_angle (degrees), color_hex, thickness, opacity

3. POLYLINE - Connected series of line segments. See attached "POLYLINE stroke sample" image showing 5 examples with varying point counts, path shapes, and thickness.
   Example: {{"type": "polyline", "points": [[100,100], [150,200], [200,150], [250,250]], "color_hex": "#22AA44", "thickness": 4, "opacity": 0.7}}
   Required fields: type, points (list of [x,y] coordinates), color_hex, thickness, opacity

4. CIRCLE - Circle (outline or filled). See attached "CIRCLE stroke sample" image showing 5 examples with varying radii, fill modes, and opacity.
   Example: {{"type": "circle", "center_x": 400, "center_y": 300, "radius": 50, "fill": true, "color_hex": "#FFAA00", "thickness": 2, "opacity": 0.6}}
   Required fields: type, center_x, center_y, radius, fill (true/false), color_hex, thickness, opacity

5. SPLATTER - Random dots within a radius (texture effect). See attached "SPLATTER stroke sample" image showing 5 examples with varying radius, dot count, and dot sizes.
   Example: {{"type": "splatter", "center_x": 200, "center_y": 150, "splatter_radius": 30, "splatter_count": 15, "dot_size_min": 2, "dot_size_max": 6, "color_hex": "#8B4513", "thickness": 1, "opacity": 0.5}}
   Required fields: type, center_x, center_y, splatter_radius, splatter_count, dot_size_min, dot_size_max, color_hex, thickness, opacity

6. DRY-BRUSH - Bristle-textured stroke with gaps showing canvas through. See attached "DRY-BRUSH stroke sample" image.
   Example: {{"type": "dry-brush", "points": [[100,100], [300,200], [500,150]], "brush_width": 30, "bristle_count": 8, "gap_probability": 0.3, "color_hex": "#8B4513", "thickness": 20, "opacity": 0.8}}
   Required fields: type, points (list of [x,y] coordinates, 2-50 points), brush_width (4-100), bristle_count (3-20), gap_probability (0.0-0.7), color_hex, thickness, opacity

7. CHALK - Grainy, textured stroke like chalk or pastel on rough paper. See attached "CHALK stroke sample" image.
   Example: {{"type": "chalk", "points": [[150,200], [350,180], [450,250]], "chalk_width": 20, "grain_density": 4, "color_hex": "#D2691E", "thickness": 1, "opacity": 0.7}}
   Required fields: type, points (list of [x,y] coordinates, 2-50 points), chalk_width (2-60), grain_density (1-8), color_hex, thickness, opacity

Canvas dimensions: {CANVAS_WIDTH}x{CANVAS_HEIGHT} pixels
All coordinates must be within bounds (0 to {CANVAS_WIDTH} for x, 0 to {CANVAS_HEIGHT} for y).
Use 0 for the left/top edge and {CANVAS_WIDTH}/{CANVAS_HEIGHT} for the right/bottom edge.

Stroke constraints:
- Thickness: {MIN_STROKE_THICKNESS} to {MAX_STROKE_THICKNESS} pixels
- Opacity: {MIN_STROKE_OPACITY} to {MAX_STROKE_OPACITY} (0.0 = transparent, 1.0 = opaque)

Consider:
- {artist_name}'s characteristic techniques, color palette, and composition style
- The current state of the canvas and how to build upon it
- Creating cohesive, original artwork (not copying specific existing pieces)
- Using varied stroke types to achieve different artistic effects
- Use dry-brush and chalk for textured, painterly effects

RESPONSE FORMAT (JSON only):
{{
  "strokes": [
    // {num_strokes} stroke object(s) here - each must include all required fields for its type
  ],
  "updated_strategy": "<optional strategy update for future iterations, or null>",
  "batch_reasoning": "<REQUIRED: explanation for this batch of strokes>"{layer_complete_field}
}}

IMPORTANT: Respond ONLY with valid JSON. Do not include any markdown formatting, code blocks, or text before/after the JSON."""

        return prompt

    def _parse_stroke_response(self, response_text: str) -> StrokeVLMResponse:
        """
        Parse VLM response into StrokeVLMResponse with multiple strokes.

        Args:
            response_text (str): Raw VLM response

        Returns:
            StrokeVLMResponse: Parsed stroke response with list of strokes

        Raises:
            ValueError: If JSON invalid or missing critical fields
            json.JSONDecodeError: If not valid JSON
        """
        # Use shared robust JSON parsing utility
        data = clean_and_parse_json(response_text)

        # Handle both old format (single stroke) and new format (strokes array) for backward compatibility
        strokes_list: list[dict[str, Any]] = []
        batch_reasoning = ""

        if "strokes" in data:
            # New format: array of strokes with batch_reasoning
            if not isinstance(data["strokes"], list):
                logger.warning("Response 'strokes' field is not a list, treating as empty")
                strokes_list = []
            else:
                strokes_list = data["strokes"]

            batch_reasoning = data.get("batch_reasoning", "")
            if not batch_reasoning:
                logger.warning("Response missing 'batch_reasoning' field")
                batch_reasoning = "No reasoning provided"

        elif "stroke" in data:
            # Old format: single stroke with reasoning - convert to new format
            logger.info("Detected old single-stroke format, converting to multi-stroke format")
            strokes_list = [data["stroke"]]
            batch_reasoning = data["stroke"].get("reasoning", "Legacy single stroke")

        else:
            raise ValueError("Response missing both 'strokes' and 'stroke' fields")

        # Parse and validate each stroke
        parsed_strokes = []
        for idx, stroke in enumerate(strokes_list):
            if not isinstance(stroke, dict):
                logger.warning(f"Skipping stroke {idx}: not a dictionary")
                continue

            if "type" not in stroke:
                logger.warning(f"Skipping stroke {idx}: missing 'type' field")
                continue

            try:
                # Parse stroke fields with type conversion
                parsed_stroke = self._parse_single_stroke(stroke)
                parsed_strokes.append(parsed_stroke)
            except (ValueError, KeyError, TypeError) as e:
                logger.warning(f"Skipping stroke {idx}: parsing error - {e}")
                continue

        # If no strokes were successfully parsed, log warning
        if not parsed_strokes:
            logger.warning("No valid strokes parsed from VLM response")

        # Build response
        response: StrokeVLMResponse = {
            "strokes": parsed_strokes,
            "updated_strategy": data.get("updated_strategy"),
            "batch_reasoning": batch_reasoning,
        }

        # Forward layer_complete if present in VLM response
        if "layer_complete" in data:
            response["layer_complete"] = bool(data["layer_complete"])

        return response

    def _parse_single_stroke(self, stroke: dict[str, Any]) -> Stroke:
        """
        Parse a single stroke dictionary with type-specific field handling.

        Args:
            stroke (dict[str, Any]): Raw stroke data from VLM

        Returns:
            Stroke: Parsed stroke with proper types

        Raises:
            ValueError: If required fields are missing or invalid
            KeyError: If critical field is missing
        """
        stroke_type = stroke["type"]

        # Core fields (all stroke types)
        parsed: Stroke = {
            "type": stroke_type,
            "color_hex": str(stroke["color_hex"]),
            "thickness": int(stroke.get("thickness", 1)),
            "opacity": float(stroke["opacity"]),
        }

        # Type-specific fields with validation
        if stroke_type == "line":
            parsed.update(
                {
                    "start_x": int(stroke["start_x"]),
                    "start_y": int(stroke["start_y"]),
                    "end_x": int(stroke["end_x"]),
                    "end_y": int(stroke["end_y"]),
                }
            )

        elif stroke_type == "arc":
            parsed.update(
                {
                    "arc_bbox": stroke["arc_bbox"],  # Expected as list [x0, y0, x1, y1]
                    "arc_start_angle": int(stroke["arc_start_angle"]),
                    "arc_end_angle": int(stroke["arc_end_angle"]),
                }
            )

        elif stroke_type == "polyline":
            parsed["points"] = stroke["points"]  # Expected as list of [x, y] pairs

        elif stroke_type == "circle":
            parsed.update(
                {
                    "center_x": int(stroke["center_x"]),
                    "center_y": int(stroke["center_y"]),
                    "radius": int(stroke["radius"]),
                    "fill": bool(stroke.get("fill", False)),
                }
            )

        elif stroke_type == "splatter":
            parsed.update(
                {
                    "center_x": int(stroke["center_x"]),
                    "center_y": int(stroke["center_y"]),
                    "splatter_radius": int(stroke["splatter_radius"]),
                    "splatter_count": int(stroke["splatter_count"]),
                    "dot_size_min": int(stroke["dot_size_min"]),
                    "dot_size_max": int(stroke["dot_size_max"]),
                }
            )

        else:
            raise ValueError(f"Unknown stroke type: {stroke_type}")

        return parsed

    def _record_interaction(
        self,
        iteration: int,
        artist_name: str,
        subject: str,
        prompt: str,
        raw_response: str,
        parsed_response: StrokeVLMResponse,
        num_strokes_requested: int,
        num_strokes_parsed: int,
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
            num_strokes_requested (int): Number of strokes requested from VLM
            num_strokes_parsed (int): Number of strokes successfully parsed
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
            "num_strokes_requested": num_strokes_requested,
            "num_strokes_parsed": num_strokes_parsed,
        }
        self.interaction_history.append(interaction)
        logger.debug(
            f"Recorded interaction for iteration {iteration}: "
            f"{num_strokes_parsed}/{num_strokes_requested} strokes parsed"
        )

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
