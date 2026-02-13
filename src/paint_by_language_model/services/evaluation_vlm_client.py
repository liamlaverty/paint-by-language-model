"""Evaluation VLM Client for assessing artistic style similarity."""

import json
import logging
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from models import PaintingPlan, PlanLayer

from config import API_BASE_URL, API_KEY, EVALUATION_PROMPT_TEMPERATURE, VLM_MODEL, VLM_TIMEOUT
from models.evaluation_result import EvaluationResult
from vlm_client import VLMClient

logger = logging.getLogger(__name__)


class EvaluationVLMClient:
    """Client for querying VLMs to evaluate artistic style."""

    def __init__(
        self,
        base_url: str = API_BASE_URL,
        model: str = VLM_MODEL,
        timeout: int = VLM_TIMEOUT,
        api_key: str = API_KEY,
        temperature: float = EVALUATION_PROMPT_TEMPERATURE,
    ):
        """
        Initialize Evaluation VLM Client.

        Args:
            base_url (str): VLM API server URL
            model (str): VLM model identifier
            timeout (int): Request timeout in seconds
            api_key (str): API key for authentication
            temperature (float): Sampling temperature for evaluation (lower = more consistent)
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

        # Storage for interaction history (for debugging and tracing)
        self.interaction_history: list[dict[str, Any]] = []
        self.last_raw_response: str | None = None
        self.last_parsed_response: EvaluationResult | None = None

        logger.info(f"Initialized EvaluationVLMClient with model: {model}")

    def evaluate_style(
        self,
        canvas_image: bytes,
        artist_name: str,
        subject: str,
        iteration: int,
        painting_plan: "PaintingPlan | None" = None,
        current_layer: "PlanLayer | None" = None,
    ) -> EvaluationResult:
        """
        Evaluate canvas style similarity to target artist.

        Args:
            canvas_image (bytes): Current canvas as image bytes
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number
            painting_plan (PaintingPlan | None): Complete painting plan
            current_layer (PlanLayer | None): Current layer information

        Returns:
            EvaluationResult: Evaluation score and feedback

        Raises:
            ConnectionError: If VLM server unreachable
            ValueError: If response cannot be parsed
            RuntimeError: For other VLM errors
        """
        logger.info(f"Requesting style evaluation for iteration {iteration}")

        # Build prompt
        prompt = self._build_evaluation_prompt(
            artist_name=artist_name,
            subject=subject,
            iteration=iteration,
            painting_plan=painting_plan,
            current_layer=current_layer,
        )

        # Query VLM
        try:
            response_text = self.client.query_multimodal(prompt=prompt, image_bytes=canvas_image)

            # Parse response
            evaluation = self._parse_evaluation_response(
                response_text=response_text,
                iteration=iteration,
                current_layer=current_layer,
            )

            # Store raw and parsed responses
            self.last_raw_response = response_text
            self.last_parsed_response = evaluation

            # Store in interaction history
            self._record_interaction(
                iteration=iteration,
                artist_name=artist_name,
                subject=subject,
                prompt=prompt,
                raw_response=response_text,
                parsed_response=evaluation,
            )

            logger.info(f"Evaluation score: {evaluation['score']:.1f}/100")
            return evaluation

        except ConnectionError:
            logger.error("Failed to connect to VLM server")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse VLM response as JSON: {e}")
            logger.debug(f"Raw response: {response_text}")
            raise ValueError(f"VLM returned invalid JSON: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during VLM evaluation: {e}")
            raise RuntimeError(f"VLM evaluation failed: {e}") from e

    def _build_evaluation_prompt(
        self,
        artist_name: str,
        subject: str,
        iteration: int,
        painting_plan: "PaintingPlan | None" = None,
        current_layer: "PlanLayer | None" = None,
    ) -> str:
        """
        Build prompt for style evaluation.

        Args:
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number
            painting_plan (PaintingPlan | None): Complete painting plan
            current_layer (PlanLayer | None): Current layer information

        Returns:
            str: Formatted prompt
        """
        # Build layer context section if available
        layer_section = ""
        response_format_addition = ""
        if painting_plan and current_layer:
            layer_number = current_layer["layer_number"]
            layer_name = current_layer["name"]
            total_layers = painting_plan["total_layers"]
            
            layer_section = f"""

You are also evaluating progress on Layer {layer_number}: "{layer_name}".
The overall plan has {total_layers} layers.

Consider whether this layer's objectives have been adequately achieved:
- {current_layer["description"]}
- Expected palette: {', '.join(current_layer["colour_palette"])}
- Expected techniques: {current_layer["techniques"]}
"""
            response_format_addition = ',\n  "layer_complete": <boolean - true if this layer\'s objectives are sufficiently met>'

        prompt = f"""You are an art critic evaluating artwork for stylistic similarity to {artist_name}.

Current Canvas: [Image attached]
Subject: {subject}
Iteration: {iteration}{layer_section}

Task: Rate how well this image embodies {artist_name}'s artistic style on a scale of 0-100.

Consider:
- Color palette characteristic of {artist_name}
- Brushwork and technique
- Compositional style
- Emotional/atmospheric qualities
- Overall aesthetic coherence

Be critical but fair. A score of 0-20 means no resemblance, 21-40 means slight resemblance,
41-60 means moderate resemblance, 61-80 means strong resemblance, and 81-100 means exceptional resemblance.

Respond in JSON format:
{{
  "score": <float 0-100>,
  "feedback": "<detailed qualitative assessment>",
  "strengths": "<what's working well stylistically>",
  "suggestions": "<areas that could be improved>"{response_format_addition}
}}

IMPORTANT: Respond ONLY with valid JSON. Do not include any text before or after the JSON object."""

        return prompt

    def _parse_evaluation_response(
        self,
        response_text: str,
        iteration: int,
        current_layer: "PlanLayer | None" = None,
    ) -> EvaluationResult:
        """
        Parse VLM evaluation response into EvaluationResult.

        Args:
            response_text (str): Raw VLM response
            iteration (int): Current iteration number
            current_layer (PlanLayer | None): Current layer information

        Returns:
            EvaluationResult: Parsed evaluation

        Raises:
            ValueError: If JSON invalid, missing fields, or score out of range
            json.JSONDecodeError: If not valid JSON
        """
        # Try to extract JSON if VLM included extra text
        json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
        json_text = json_match.group(0) if json_match else response_text

        # Try parsing as-is first
        try:
            data = json.loads(json_text)
        except json.JSONDecodeError as e:
            # If that fails, try cleaning control characters in a more sophisticated way
            # Remove or escape control characters that break JSON
            logger.warning(f"Initial JSON parse failed: {e}. Attempting to clean response.")

            # Replace problematic control characters
            cleaned_json = re.sub(r"[\x00-\x1f\x7f-\x9f]", " ", json_text)

            try:
                data = json.loads(cleaned_json)
                logger.info("Successfully parsed after cleaning control characters")
            except json.JSONDecodeError as e2:
                logger.error(f"Failed to parse JSON even after cleaning: {e2}")
                logger.debug(f"Original response: {json_text[:500]}")
                logger.debug(f"Cleaned response: {cleaned_json[:500]}")
                raise ValueError(f"VLM returned invalid JSON: {e2}") from e2

        # Validate required fields
        required_fields = ["score", "feedback", "strengths", "suggestions"]
        for field in required_fields:
            if field not in data:
                raise ValueError(f"Evaluation missing required field: {field}")

        # Validate score range
        score = float(data["score"])
        if not 0 <= score <= 100:
            raise ValueError(f"Score {score} out of valid range [0, 100]")

        # Build result
        result: EvaluationResult = {
            "score": score,
            "feedback": str(data["feedback"]),
            "strengths": str(data["strengths"]),
            "suggestions": str(data["suggestions"]),
            "timestamp": datetime.now().isoformat(),
            "iteration": iteration,
        }

        # Add layer-specific fields if layer context was provided
        if current_layer:
            result["layer_complete"] = data.get("layer_complete", False)
            result["layer_number"] = current_layer["layer_number"]

        return result

    def _record_interaction(
        self,
        iteration: int,
        artist_name: str,
        subject: str,
        prompt: str,
        raw_response: str,
        parsed_response: EvaluationResult,
    ) -> None:
        """
        Record an interaction in the history for tracing and debugging.

        Args:
            iteration (int): Iteration number
            artist_name (str): Target artist name
            subject (str): Subject being painted
            prompt (str): The prompt sent to the VLM
            raw_response (str): Raw VLM response text
            parsed_response (EvaluationResult): Parsed evaluation response
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
        logger.debug(f"Recorded evaluation interaction for iteration {iteration}")

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
        logger.info("Cleared evaluation interaction history")
