"""Verify all config settings can be imported and have valid values."""

import sys
import unittest
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).parent.parent / "src" / "paint_by_language_model")
)

import config


class TestConfigSettings(unittest.TestCase):
    """Test configuration settings."""

    def test_phase1_settings_exist(self) -> None:
        """Test Phase 1 settings are present."""
        self.assertTrue(hasattr(config, "LMSTUDIO_BASE_URL"))
        self.assertTrue(hasattr(config, "LMSTUDIO_MODEL"))
        self.assertTrue(hasattr(config, "REQUEST_TIMEOUT"))
        self.assertTrue(hasattr(config, "MAX_TOKENS"))

    def test_phase2_canvas_settings_exist(self) -> None:
        """Test Phase 2 canvas settings are present."""
        self.assertTrue(hasattr(config, "CANVAS_WIDTH"))
        self.assertTrue(hasattr(config, "CANVAS_HEIGHT"))
        self.assertTrue(hasattr(config, "CANVAS_BACKGROUND_COLOR"))

    def test_phase2_stroke_settings_exist(self) -> None:
        """Test Phase 2 stroke settings are present."""
        self.assertTrue(hasattr(config, "MAX_STROKE_THICKNESS"))
        self.assertTrue(hasattr(config, "MIN_STROKE_THICKNESS"))
        self.assertTrue(hasattr(config, "MAX_STROKE_OPACITY"))
        self.assertTrue(hasattr(config, "MIN_STROKE_OPACITY"))
        self.assertTrue(hasattr(config, "SUPPORTED_STROKE_TYPES"))

    def test_phase2_vlm_settings_exist(self) -> None:
        """Test Phase 2 VLM settings are present."""
        self.assertTrue(hasattr(config, "VLM_MODEL"))
        self.assertTrue(hasattr(config, "VLM_TIMEOUT"))
        self.assertTrue(hasattr(config, "EVALUATION_VLM_MODEL"))
        self.assertTrue(hasattr(config, "STROKE_PROMPT_TEMPERATURE"))
        self.assertTrue(hasattr(config, "EVALUATION_PROMPT_TEMPERATURE"))

    def test_phase2_generation_settings_exist(self) -> None:
        """Test Phase 2 generation settings are present."""
        self.assertTrue(hasattr(config, "MAX_ITERATIONS"))
        self.assertTrue(hasattr(config, "MIN_ITERATIONS"))
        self.assertTrue(hasattr(config, "TARGET_STYLE_SCORE"))
        self.assertTrue(hasattr(config, "MIN_STYLE_SCORE_IMPROVEMENT"))

    def test_phase2_strategy_settings_exist(self) -> None:
        """Test Phase 2 strategy settings are present."""
        self.assertTrue(hasattr(config, "STRATEGY_CONTEXT_WINDOW"))
        self.assertTrue(hasattr(config, "STRATEGY_DIR_NAME"))
        self.assertTrue(hasattr(config, "STROKE_PROMPT_INCLUDE_STRATEGY"))

    def test_phase2_output_settings_exist(self) -> None:
        """Test Phase 2 output settings are present."""
        self.assertTrue(hasattr(config, "OUTPUT_STRUCTURE"))
        self.assertTrue(isinstance(config.OUTPUT_STRUCTURE, dict))
        self.assertTrue(hasattr(config, "IMAGE_EXPORT_FORMATS"))
        self.assertTrue(hasattr(config, "SNAPSHOT_FORMAT"))

    def test_phase2_logging_settings_exist(self) -> None:
        """Test Phase 2 logging settings are present."""
        self.assertTrue(hasattr(config, "GENERATION_LOG_LEVEL"))
        self.assertTrue(hasattr(config, "LOG_VLM_RAW_RESPONSES"))

    def test_phase2_performance_settings_exist(self) -> None:
        """Test Phase 2 performance settings are present."""
        self.assertTrue(hasattr(config, "RESIZE_FOR_VLM"))
        self.assertTrue(hasattr(config, "VLM_IMAGE_MAX_DIMENSION"))

    def test_phase2_validation_settings_exist(self) -> None:
        """Test Phase 2 validation settings are present."""
        self.assertTrue(hasattr(config, "STRICT_STROKE_VALIDATION"))
        self.assertTrue(hasattr(config, "ALLOW_ZERO_LENGTH_STROKES"))
        self.assertTrue(hasattr(config, "COLOR_HEX_PATTERN"))

    def test_phase5_gif_settings_exist(self) -> None:
        """Test Phase 5 GIF generation settings are present."""
        self.assertTrue(hasattr(config, "GIF_FRAME_DURATION_MS"))
        self.assertTrue(hasattr(config, "GIF_FINAL_FRAME_HOLD_MS"))
        self.assertTrue(hasattr(config, "GIF_MAX_DIMENSION"))
        self.assertTrue(hasattr(config, "GIF_FILENAME"))
        self.assertTrue(hasattr(config, "GIF_LOOP_COUNT"))

    def test_canvas_dimensions_positive(self) -> None:
        """Test canvas dimensions are positive integers."""
        self.assertGreater(config.CANVAS_WIDTH, 0)
        self.assertGreater(config.CANVAS_HEIGHT, 0)
        self.assertIsInstance(config.CANVAS_WIDTH, int)
        self.assertIsInstance(config.CANVAS_HEIGHT, int)

    def test_stroke_thickness_range_valid(self) -> None:
        """Test stroke thickness range is valid."""
        self.assertGreater(config.MAX_STROKE_THICKNESS, 0)
        self.assertGreater(config.MIN_STROKE_THICKNESS, 0)
        self.assertGreaterEqual(
            config.MAX_STROKE_THICKNESS, config.MIN_STROKE_THICKNESS
        )

    def test_stroke_opacity_range_valid(self) -> None:
        """Test stroke opacity range is valid."""
        self.assertGreaterEqual(config.MAX_STROKE_OPACITY, 0.0)
        self.assertLessEqual(config.MAX_STROKE_OPACITY, 1.0)
        self.assertGreaterEqual(config.MIN_STROKE_OPACITY, 0.0)
        self.assertLessEqual(config.MIN_STROKE_OPACITY, 1.0)
        self.assertGreaterEqual(config.MAX_STROKE_OPACITY, config.MIN_STROKE_OPACITY)

    def test_iteration_limits_valid(self) -> None:
        """Test iteration limits are valid."""
        self.assertGreater(config.MAX_ITERATIONS, 0)
        self.assertGreater(config.MIN_ITERATIONS, 0)
        self.assertGreaterEqual(config.MAX_ITERATIONS, config.MIN_ITERATIONS)

    def test_target_score_in_range(self) -> None:
        """Test target score is in valid range."""
        self.assertGreaterEqual(config.TARGET_STYLE_SCORE, 0)
        self.assertLessEqual(config.TARGET_STYLE_SCORE, 100)

    def test_timeout_values_positive(self) -> None:
        """Test timeout values are positive."""
        self.assertGreater(config.REQUEST_TIMEOUT, 0)
        self.assertGreater(config.VLM_TIMEOUT, 0)

    def test_strategy_window_positive(self) -> None:
        """Test strategy window is positive."""
        self.assertGreater(config.STRATEGY_CONTEXT_WINDOW, 0)

    def test_paths_are_path_objects(self) -> None:
        """Test file paths are Path objects."""
        self.assertIsInstance(config.PROJECT_ROOT, Path)
        self.assertIsInstance(config.ARTISTS_FILE, Path)
        self.assertIsInstance(config.OUTPUT_DIR, Path)

    def test_color_hex_pattern_valid(self) -> None:
        """Test color hex pattern exists."""
        self.assertTrue(hasattr(config, "COLOR_HEX_PATTERN"))
        self.assertIsInstance(config.COLOR_HEX_PATTERN, str)

    def test_output_structure_complete(self) -> None:
        """Test output structure has all required keys."""
        required_keys = [
            "snapshots",
            "strategies",
            "evaluations",
            "strokes",
            "metadata",
            "final_artwork",
            "report",
        ]
        for key in required_keys:
            self.assertIn(key, config.OUTPUT_STRUCTURE)

    def test_temperature_values_valid(self) -> None:
        """Test temperature values are in valid range."""
        self.assertGreaterEqual(config.STROKE_PROMPT_TEMPERATURE, 0.0)
        self.assertLessEqual(config.STROKE_PROMPT_TEMPERATURE, 2.0)
        self.assertGreaterEqual(config.EVALUATION_PROMPT_TEMPERATURE, 0.0)
        self.assertLessEqual(config.EVALUATION_PROMPT_TEMPERATURE, 2.0)

    def test_supported_stroke_types_is_list(self) -> None:
        """Test supported stroke types is a list."""
        self.assertIsInstance(config.SUPPORTED_STROKE_TYPES, list)
        self.assertGreater(len(config.SUPPORTED_STROKE_TYPES), 0)

    def test_image_export_formats_is_list(self) -> None:
        """Test image export formats is a list."""
        self.assertIsInstance(config.IMAGE_EXPORT_FORMATS, list)
        self.assertGreater(len(config.IMAGE_EXPORT_FORMATS), 0)

    def test_gif_settings_valid(self) -> None:
        """Test GIF generation settings have valid values."""
        self.assertGreater(config.GIF_FRAME_DURATION_MS, 0)
        self.assertGreater(config.GIF_FINAL_FRAME_HOLD_MS, 0)
        self.assertGreater(config.GIF_MAX_DIMENSION, 0)
        self.assertIsInstance(config.GIF_FILENAME, str)
        self.assertTrue(config.GIF_FILENAME.endswith(".gif"))
        self.assertGreaterEqual(config.GIF_LOOP_COUNT, 0)

    def test_provider_config_exists(self) -> None:
        """Provider configuration constants exist."""
        self.assertTrue(hasattr(config, "PROVIDER"))
        self.assertTrue(hasattr(config, "API_BASE_URL"))
        self.assertTrue(hasattr(config, "API_KEY"))
        self.assertTrue(hasattr(config, "DEFAULT_MODEL"))

    def test_mistral_config_exists(self) -> None:
        """Mistral-specific constants exist."""
        self.assertTrue(hasattr(config, "MISTRAL_BASE_URL"))
        self.assertTrue(hasattr(config, "MISTRAL_API_KEY"))
        self.assertTrue(hasattr(config, "MISTRAL_VLM_MODEL"))
        self.assertTrue(hasattr(config, "MISTRAL_EVALUATION_VLM_MODEL"))

    def test_lmstudio_config_exists(self) -> None:
        """LMStudio-specific constants still exist for local dev."""
        self.assertTrue(hasattr(config, "LMSTUDIO_BASE_URL"))
        self.assertTrue(hasattr(config, "LMSTUDIO_MODEL"))
        self.assertTrue(hasattr(config, "LMSTUDIO_VLM_MODEL"))

    def test_provider_resolves_correctly(self) -> None:
        """API_BASE_URL matches PROVIDER setting."""
        if config.PROVIDER == "mistral":
            self.assertEqual(config.API_BASE_URL, config.MISTRAL_BASE_URL)
        else:
            self.assertEqual(config.API_BASE_URL, config.LMSTUDIO_BASE_URL)


if __name__ == "__main__":
    unittest.main()
