"""Stroke VLM Client for querying VLMs for stroke suggestions."""

import json
import logging
from datetime import datetime
from pathlib import Path
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
from models.stroke_vlm_response import StrokeVLMResponse
from services.prompt_logger import PromptLogger
from services.stroke_parser import StrokeParser
from services.stroke_sample_generator import StrokeSampleGenerator
from vlm_client import VLMClient

logger = logging.getLogger(__name__)

_STROKE_PROMPT_TEMPLATE_PATH = (
    Path(__file__).parent.parent.parent.parent / "datafiles" / "prompts" / "stroke_prompt.txt"
)


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
        allowed_stroke_types: list[str] | None = None,
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
            allowed_stroke_types (list[str] | None): Restrict which stroke types
                appear in the AVAILABLE STROKE TYPES prompt block.  When ``None``
                or an empty list, all ten stroke types are included (existing
                behaviour preserved).

        The stroke prompt template is loaded once from
        ``_STROKE_PROMPT_TEMPLATE_PATH`` and cached as
        ``self._stroke_prompt_template`` for the lifetime of the instance.
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
        self.allowed_stroke_types = allowed_stroke_types

        # Storage for interaction history (for debugging and tracing)
        self.interaction_history: list[dict[str, Any]] = []
        self.last_raw_response: str | None = None
        self.last_parsed_response: StrokeVLMResponse | None = None

        logger.info(f"Initialized StrokeVLMClient with model: {model}")

        self.parser = StrokeParser()
        self.sample_generator = StrokeSampleGenerator()
        self._stroke_samples = self.sample_generator.generate_all_samples()
        logger.info(f"Generated {len(self._stroke_samples)} stroke sample images")

        self._stroke_prompt_template: str = _STROKE_PROMPT_TEMPLATE_PATH.read_text(encoding="utf-8")

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
            allowed_lower = (
                [t.lower() for t in self.allowed_stroke_types]
                if self.allowed_stroke_types
                else None
            )
            for stroke_type, sample_bytes in self._stroke_samples.items():
                if allowed_lower is None or stroke_type.lower() in allowed_lower:
                    images.append((sample_bytes, f"{stroke_type.upper()} stroke sample"))
            logger.debug(
                f"Attaching {len(images) - 1} stroke sample image(s) "
                f"(allowed: {self.allowed_stroke_types or 'all'})"
            )

            response_text = self.client.query_multimodal_multi_image(
                prompt=prompt,
                images=images,
            )

            # Store raw response immediately so it is always available,
            # even if parsing fails below.
            self.last_raw_response = response_text

            # Parse response
            stroke_response = self.parser.parse(response_text)

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
                    if allowed_lower is None or stroke_type.lower() in allowed_lower:
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
            str: Formatted prompt string produced by rendering the template at
                ``_STROKE_PROMPT_TEMPLATE_PATH`` via ``str.format_map``.
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

        stroke_types_section = self._build_stroke_types_section()

        # Build conditional Consider lines for specific stroke types
        allowed_lower = (
            [t.lower() for t in self.allowed_stroke_types] if self.allowed_stroke_types else None
        )
        dry_chalk_consider = ""
        if allowed_lower is None or "dry-brush" in allowed_lower or "chalk" in allowed_lower:
            dry_chalk_consider = "\n- Use dry-brush and chalk for textured, painterly effects"
        wet_brush_consider = ""
        if allowed_lower is None or "wet-brush" in allowed_lower:
            wet_brush_consider = (
                "\n- Use wet-brush for soft watercolour bleeds and ink-wash effects"
            )

        return self._stroke_prompt_template.format_map(
            {
                "artist_name": artist_name,
                "subject_section": subject_section,
                "iteration": iteration,
                "strategy_section": strategy_section,
                "plan_section": plan_section,
                "num_strokes": num_strokes,
                "stroke_types_section": stroke_types_section,
                "canvas_width": CANVAS_WIDTH,
                "canvas_height": CANVAS_HEIGHT,
                "min_stroke_thickness": MIN_STROKE_THICKNESS,
                "max_stroke_thickness": MAX_STROKE_THICKNESS,
                "min_stroke_opacity": MIN_STROKE_OPACITY,
                "max_stroke_opacity": MAX_STROKE_OPACITY,
                "dry_chalk_consider": dry_chalk_consider,
                "wet_brush_consider": wet_brush_consider,
                "layer_complete_field": layer_complete_field,
            }
        )

    def _build_stroke_types_section(self) -> str:
        """
        Build the ``AVAILABLE STROKE TYPES`` block, filtered to allowed types.

        Uses ``self.allowed_stroke_types`` to restrict which entries appear.
        When ``self.allowed_stroke_types`` is ``None`` or an empty list all ten
        stroke type entries are included (existing behaviour preserved).  The
        remaining entries are re-numbered sequentially starting from 1 so that
        the prompt contains no gaps.

        Returns:
            str: The fully assembled ``AVAILABLE STROKE TYPES`` section string,
                including the section heading.
        """
        all_entries: list[tuple[str, str]] = [
            (
                "line",
                'LINE - Straight line between two points. See attached "LINE stroke sample"'
                " image showing 5 examples with varying thickness, colour, opacity, and angle.\n"
                '   Example: {"type": "line", "start_x": 100, "start_y": 200,'
                ' "end_x": 300, "end_y": 400, "color_hex": "#FF5733", "thickness": 5, "opacity": 0.8}\n'
                "   Required fields: type, start_x, start_y, end_x, end_y, color_hex, thickness, opacity",
            ),
            (
                "arc",
                'ARC - Curved arc within a bounding box. See attached "ARC stroke sample"'
                " image showing 5 examples with varying bbox sizes, angle sweeps, and thickness.\n"
                '   Example: {"type": "arc", "arc_bbox": [50, 50, 250, 250],'
                ' "arc_start_angle": 0, "arc_end_angle": 180, "color_hex": "#3366CC",'
                ' "thickness": 3, "opacity": 0.9}\n'
                "   Required fields: type, arc_bbox (list [x0,y0,x1,y1]),"
                " arc_start_angle (degrees), arc_end_angle (degrees), color_hex, thickness, opacity",
            ),
            (
                "polyline",
                'POLYLINE - Connected series of line segments. See attached "POLYLINE stroke sample"'
                " image showing 5 examples with varying point counts, path shapes, and thickness.\n"
                '   Example: {"type": "polyline", "points": [[100,100], [150,200], [200,150], [250,250]],'
                ' "color_hex": "#22AA44", "thickness": 4, "opacity": 0.7}\n'
                "   Required fields: type, points (list of [x,y] coordinates), color_hex, thickness, opacity",
            ),
            (
                "circle",
                'CIRCLE - Circle (outline or filled). See attached "CIRCLE stroke sample"'
                " image showing 5 examples with varying radii, fill modes, and opacity.\n"
                '   Example: {"type": "circle", "center_x": 400, "center_y": 300,'
                ' "radius": 50, "fill": true, "color_hex": "#FFAA00", "thickness": 2, "opacity": 0.6}\n'
                "   Required fields: type, center_x, center_y, radius, fill (true/false),"
                " color_hex, thickness, opacity",
            ),
            (
                "splatter",
                'SPLATTER - Random dots within a radius (texture effect). See attached "SPLATTER stroke sample"'
                " image showing 5 examples with varying radius, dot count, and dot sizes.\n"
                '   Example: {"type": "splatter", "center_x": 200, "center_y": 150,'
                ' "splatter_radius": 30, "splatter_count": 15, "dot_size_min": 2, "dot_size_max": 6,'
                ' "color_hex": "#8B4513", "thickness": 1, "opacity": 0.5}\n'
                "   Required fields: type, center_x, center_y, splatter_radius, splatter_count,"
                " dot_size_min, dot_size_max, color_hex, thickness, opacity",
            ),
            (
                "dry-brush",
                "DRY-BRUSH - Bristle-textured stroke with gaps showing canvas through."
                ' See attached "DRY-BRUSH stroke sample" image.\n'
                '   Example: {"type": "dry-brush", "points": [[100,100], [300,200], [500,150]],'
                ' "brush_width": 30, "bristle_count": 8, "gap_probability": 0.3,'
                ' "color_hex": "#8B4513", "thickness": 20, "opacity": 0.8}\n'
                "   Required fields: type, points (list of [x,y] coordinates, 2-50 points),"
                " brush_width (4-100), bristle_count (3-20), gap_probability (0.0-0.7),"
                " color_hex, thickness, opacity",
            ),
            (
                "chalk",
                "CHALK - Grainy, textured stroke like chalk or pastel on rough paper."
                ' See attached "CHALK stroke sample" image.\n'
                '   Example: {"type": "chalk", "points": [[150,200], [350,180], [450,250]],'
                ' "chalk_width": 20, "grain_density": 4, "color_hex": "#D2691E",'
                ' "thickness": 1, "opacity": 0.7}\n'
                "   Required fields: type, points (list of [x,y] coordinates, 2-50 points),"
                " chalk_width (2-60), grain_density (1-8), color_hex, thickness, opacity",
            ),
            (
                "wet-brush",
                "WET-BRUSH - Soft-edged stroke that bleeds and spreads at its margins,"
                " characteristic of watercolour or ink-wash painting."
                ' See attached "WET-BRUSH stroke sample" image.\n'
                '   Example: {"type": "wet-brush", "points": [[100,200], [300,180], [500,220]],'
                ' "softness": 12, "flow": 0.7, "color_hex": "#4477AA",'
                ' "thickness": 14, "opacity": 0.75}\n'
                "   Required fields: type, points (list of [x,y] coordinates, 2-50 points),"
                " softness (1-30, controls blur radius), flow (0.1-1.0, controls paint density),"
                " color_hex, thickness, opacity",
            ),
            (
                "burn",
                "BURN - Darkens existing pixels in a soft circular region"
                " (shadow modelling, depth, vignetting)."
                ' See attached "BURN stroke sample" image.\n'
                '   Example: {"type": "burn", "center_x": 400, "center_y": 300,'
                ' "radius": 80, "intensity": 0.6, "color_hex": "#000000",'
                ' "thickness": 1, "opacity": 1.0}\n'
                "   Required fields: type, center_x, center_y, radius (5\u2013300),"
                " intensity (0.05\u20130.8), color_hex, thickness, opacity",
            ),
            (
                "dodge",
                "DODGE - Lightens existing pixels in a soft circular region"
                " (highlights, light sources, brightening effects)."
                ' See attached "DODGE stroke sample" image.\n'
                '   Example: {"type": "dodge", "center_x": 400, "center_y": 300,'
                ' "radius": 80, "intensity": 0.6, "color_hex": "#ffffff",'
                ' "thickness": 1, "opacity": 1.0}\n'
                "   Required fields: type, center_x, center_y, radius (5\u2013300),"
                " intensity (0.05\u20130.8), color_hex, thickness, opacity\n"
                "   Tip: Use dodge on dark areas to add highlights, simulate rim-lighting,"
                " or brighten under-exposed regions.",
            ),
        ]

        allowed_lower: list[str] | None = (
            [t.lower() for t in self.allowed_stroke_types] if self.allowed_stroke_types else None
        )

        filtered = [
            (key, desc)
            for key, desc in all_entries
            if allowed_lower is None or key in allowed_lower
        ]

        numbered_entries = [f"{i}. {desc}" for i, (_, desc) in enumerate(filtered, start=1)]

        return "AVAILABLE STROKE TYPES:\n\n" + "\n\n".join(numbered_entries)

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
