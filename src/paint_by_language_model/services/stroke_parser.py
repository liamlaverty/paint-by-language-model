"""StrokeParser — parses VLM text responses into StrokeVLMResponse objects."""

import logging
from collections.abc import Callable
from typing import Any

from models.stroke import Stroke
from models.stroke_vlm_response import StrokeVLMResponse
from utils.json_utils import clean_and_parse_json

logger = logging.getLogger(__name__)


class StrokeParser:
    """Parse raw VLM text responses into structured StrokeVLMResponse objects.

    Owns all stroke-response parsing logic, decoupled from the HTTP transport
    layer so that it can be unit-tested with plain string inputs.

    The per-type field extraction is implemented as a registry of private
    ``_apply_*`` methods, making it trivial to add new stroke types without
    modifying the core dispatch logic.
    """

    def __init__(self) -> None:
        """Initialise StrokeParser and build the stroke-type handler registry."""
        self._type_parsers: dict[str, Callable[[Stroke, dict[str, Any]], None]] = {
            "line": self._apply_line_fields,
            "arc": self._apply_arc_fields,
            "polyline": self._apply_polyline_fields,
            "circle": self._apply_circle_fields,
            "splatter": self._apply_splatter_fields,
            "dry-brush": self._apply_dry_brush_fields,
            "chalk": self._apply_chalk_fields,
            "wet-brush": self._apply_wet_brush_fields,
            "burn": self._apply_burn_dodge_fields,
            "dodge": self._apply_burn_dodge_fields,
        }

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def parse(self, response_text: str) -> StrokeVLMResponse:
        """Parse raw VLM response text into a StrokeVLMResponse.

        Handles both the current batch format (``"strokes"`` key) and the
        legacy single-stroke format (``"stroke"`` key) for backward
        compatibility.

        Args:
            response_text (str): Raw text returned by the VLM, expected to
                contain a JSON object (possibly wrapped in markdown fences).

        Returns:
            StrokeVLMResponse: Parsed response containing zero or more strokes,
                an optional strategy update, and batch reasoning text.

        Raises:
            ValueError: If the JSON is syntactically valid but missing both
                ``"strokes"`` and ``"stroke"`` keys.
            json.JSONDecodeError: If ``response_text`` cannot be parsed as JSON
                even after markdown-fence stripping.
        """
        data = clean_and_parse_json(response_text)

        strokes_list: list[dict[str, Any]] = []
        batch_reasoning = ""

        if "strokes" in data:
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
            logger.info("Detected old single-stroke format, converting to multi-stroke format")
            strokes_list = [data["stroke"]]
            batch_reasoning = data["stroke"].get("reasoning", "Legacy single stroke")

        else:
            raise ValueError("Response missing both 'strokes' and 'stroke' fields")

        parsed_strokes: list[Stroke] = []
        for idx, stroke in enumerate(strokes_list):
            if not isinstance(stroke, dict):
                logger.warning(f"Skipping stroke {idx}: not a dictionary")
                continue

            if "type" not in stroke:
                logger.warning(f"Skipping stroke {idx}: missing 'type' field")
                continue

            try:
                parsed_stroke = self._parse_single_stroke(stroke)
                parsed_strokes.append(parsed_stroke)
            except (ValueError, KeyError, TypeError) as e:
                logger.error(f"Skipping stroke {idx}: parsing error - {e}")
                continue

        if not parsed_strokes:
            logger.warning("No valid strokes parsed from VLM response")

        response: StrokeVLMResponse = {
            "strokes": parsed_strokes,
            "updated_strategy": data.get("updated_strategy"),
            "batch_reasoning": batch_reasoning,
        }

        if "layer_complete" in data:
            response["layer_complete"] = bool(data["layer_complete"])

        return response

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _parse_single_stroke(self, stroke: dict[str, Any]) -> Stroke:
        """Parse a single raw stroke dict into a typed Stroke.

        Extracts the core fields common to all stroke types, then delegates to
        the appropriate ``_apply_*`` method from the type-parser registry to
        fill in type-specific fields.

        Args:
            stroke (dict[str, Any]): Raw stroke data as returned by the VLM.

        Returns:
            Stroke: Fully populated, typed Stroke dict.

        Raises:
            ValueError: If the stroke type is not recognised or a required field
                is missing or holds an incompatible value.
            KeyError: If a mandatory field key is absent from ``stroke``.
            TypeError: If a field value cannot be coerced to the expected type.
        """
        stroke_type = stroke["type"]

        parsed: Stroke = {
            "type": stroke_type,
            "color_hex": str(stroke["color_hex"]),
            "thickness": int(stroke.get("thickness", 1)),
            "opacity": float(stroke["opacity"]),
        }

        if stroke_type not in self._type_parsers:
            raise ValueError(f"Unknown stroke type: {stroke_type}")

        self._type_parsers[stroke_type](parsed, stroke)
        return parsed

    def _apply_line_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply line-specific fields to the parsed stroke.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed.update(
            {
                "start_x": int(raw["start_x"]),
                "start_y": int(raw["start_y"]),
                "end_x": int(raw["end_x"]),
                "end_y": int(raw["end_y"]),
            }
        )

    def _apply_arc_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply arc-specific fields to the parsed stroke.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed.update(
            {
                "arc_bbox": raw["arc_bbox"],
                "arc_start_angle": int(raw["arc_start_angle"]),
                "arc_end_angle": int(raw["arc_end_angle"]),
            }
        )

    def _apply_polyline_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply polyline-specific fields to the parsed stroke.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed["points"] = raw["points"]

    def _apply_circle_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply circle-specific fields to the parsed stroke.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed.update(
            {
                "center_x": int(raw["center_x"]),
                "center_y": int(raw["center_y"]),
                "radius": int(raw["radius"]),
                "fill": bool(raw.get("fill", False)),
            }
        )

    def _apply_splatter_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply splatter-specific fields to the parsed stroke.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed.update(
            {
                "center_x": int(raw["center_x"]),
                "center_y": int(raw["center_y"]),
                "splatter_radius": int(raw["splatter_radius"]),
                "splatter_count": int(raw["splatter_count"]),
                "dot_size_min": int(raw["dot_size_min"]),
                "dot_size_max": int(raw["dot_size_max"]),
            }
        )

    def _apply_dry_brush_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply dry-brush-specific fields to the parsed stroke.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed.update(
            {
                "points": raw["points"],
                "brush_width": int(raw["brush_width"]),
                "bristle_count": int(raw["bristle_count"]),
                "gap_probability": float(raw["gap_probability"]),
            }
        )

    def _apply_chalk_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply chalk-specific fields to the parsed stroke.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed.update(
            {
                "points": raw["points"],
                "chalk_width": int(raw["chalk_width"]),
                "grain_density": int(raw["grain_density"]),
            }
        )

    def _apply_wet_brush_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply wet-brush-specific fields to the parsed stroke.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed.update(
            {
                "points": raw["points"],
                "softness": int(raw["softness"]),
                "flow": float(raw["flow"]),
            }
        )

    def _apply_burn_dodge_fields(self, parsed: Stroke, raw: dict[str, Any]) -> None:
        """Apply burn/dodge-specific fields to the parsed stroke.

        Both ``burn`` and ``dodge`` share identical field structures, so a
        single handler covers both types.

        Args:
            parsed (Stroke): Partially-built stroke dict to mutate in-place.
            raw (dict[str, Any]): Raw stroke data from the VLM response.
        """
        parsed.update(
            {
                "center_x": int(raw["center_x"]),
                "center_y": int(raw["center_y"]),
                "radius": int(raw["radius"]),
                "intensity": float(raw["intensity"]),
            }
        )
