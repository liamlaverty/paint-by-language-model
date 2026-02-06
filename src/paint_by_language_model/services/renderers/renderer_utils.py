"""Utility functions for stroke renderers."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from models import Stroke


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """
    Convert 6-digit hex color string to RGB tuple.

    Args:
        hex_color (str): Hex color string (e.g., "#FF5733")

    Returns:
        tuple[int, int, int]: RGB tuple (e.g., (255, 87, 51))
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)


def hex_to_rgba(hex_color: str) -> tuple[int, int, int, int]:
    """
    Convert 8-digit hex color string to RGBA tuple.

    Args:
        hex_color (str): Hex color string with alpha (e.g., "#FF5733CC")

    Returns:
        tuple[int, int, int, int]: RGBA tuple (e.g., (255, 87, 51, 204))
    """
    hex_color = hex_color.lstrip("#")
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    a = int(hex_color[6:8], 16)
    return (r, g, b, a)


def stroke_color_to_rgba(hex_color: str, opacity: float) -> tuple[int, int, int, int]:
    """
    Convert a stroke's hex color and opacity to an RGBA tuple.

    Handles both 6-digit (#RRGGBB) and 8-digit (#RRGGBBAA) hex formats.
    For 8-digit format, the alpha channel in the hex color is used.
    For 6-digit format, opacity is converted to alpha channel.

    Args:
        hex_color (str): Hex color string (e.g., "#FF5733" or "#FF5733CC")
        opacity (float): Opacity value (0.0 to 1.0)

    Returns:
        tuple[int, int, int, int]: RGBA tuple (e.g., (255, 87, 51, 204))
    """
    if len(hex_color) == 9:  # #RRGGBBAA format (8 hex digits + #)
        return hex_to_rgba(hex_color)
    else:  # #RRGGBB format (6 hex digits + #)
        color_rgb = hex_to_rgb(hex_color)
        alpha = int(opacity * 255)
        return color_rgb + (alpha,)


def validate_color_hex(color_hex: str) -> None:
    """
    Validate hex color format.

    Args:
        color_hex (str): Hex color string to validate

    Raises:
        ValueError: If color format is invalid
    """
    hex_pattern = re.compile(r"^#[0-9A-Fa-f]{6}([0-9A-Fa-f]{2})?$")
    if not hex_pattern.match(color_hex):
        raise ValueError(f"Invalid hex color format: {color_hex} (expected #RRGGBB or #RRGGBBAA)")


def validate_thickness(thickness: int) -> None:
    """
    Validate thickness value.

    Args:
        thickness (int): Thickness value to validate

    Raises:
        ValueError: If thickness is invalid
    """
    if not isinstance(thickness, int):
        raise ValueError(f"thickness must be an integer, got {type(thickness).__name__}")
    if not (1 <= thickness <= 50):
        raise ValueError(f"thickness {thickness} out of range [1, 50]")


def validate_opacity(opacity: float) -> None:
    """
    Validate opacity value.

    Args:
        opacity (float): Opacity value to validate

    Raises:
        ValueError: If opacity is invalid
    """
    if not isinstance(opacity, (int, float)):
        raise ValueError(f"opacity must be a number, got {type(opacity).__name__}")
    if not (0.0 <= opacity <= 1.0):
        raise ValueError(f"opacity {opacity} out of range [0.0, 1.0]")


def validate_common_stroke_fields(stroke: "Stroke") -> None:
    """
    Validate common stroke fields (color_hex, thickness, opacity).

    Args:
        stroke (Stroke): The stroke data to validate

    Raises:
        ValueError: If any common field validation fails
    """
    validate_color_hex(stroke["color_hex"])
    validate_thickness(stroke["thickness"])
    validate_opacity(stroke["opacity"])
