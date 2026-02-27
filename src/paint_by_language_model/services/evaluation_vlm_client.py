"""Evaluation VLM Client for assessing artistic style similarity."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from models import PaintingPlan, PlanLayer

from config import API_BASE_URL, API_KEY, EVALUATION_PROMPT_TEMPERATURE, VLM_MODEL, VLM_TIMEOUT
from models.evaluation_result import EvaluationResult
from services.prompt_logger import PromptLogger
from utils.json_utils import clean_and_parse_json
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
        prompt_logger: PromptLogger | None = None,
    ):
        """
        Initialize Evaluation VLM Client.

        Args:
            base_url (str): VLM API server URL
            model (str): VLM model identifier
            timeout (int): Request timeout in seconds
            api_key (str): API key for authentication
            temperature (float): Sampling temperature for evaluation (lower = more consistent)
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
        self.last_parsed_response: EvaluationResult | None = None

        logger.info(f"Initialized EvaluationVLMClient with model: {model}")

    def evaluate_style(
        self,
        canvas_image: bytes,
        artist_name: str,
        subject: str,
        iteration: int,
        painting_plan: PaintingPlan | None = None,
        current_layer: PlanLayer | None = None,
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

        # Build static instructions for system-prompt caching
        static_instructions = self._build_static_evaluation_instructions(artist_name)

        # Query VLM
        try:
            response_text = self.client.query_multimodal(
                prompt=prompt,
                image_bytes=canvas_image,
                system=static_instructions,
                cache_after_image=False,
            )

            # Store raw response immediately so it is available even if parsing fails
            self.last_raw_response = response_text

            # Parse response
            evaluation = self._parse_evaluation_response(
                response_text=response_text,
                iteration=iteration,
                current_layer=current_layer,
            )

            # Store parsed response
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

            if self.prompt_logger:
                self.prompt_logger.log_interaction(
                    prompt_type="evaluation",
                    prompt=prompt,
                    raw_response=response_text,
                    model=self.model,
                    provider=self.client.provider,
                    temperature=self.client.temperature,
                    images=[{"label": "Current canvas", "size_bytes": len(canvas_image)}],
                    context={
                        "iteration": iteration,
                        "artist_name": artist_name,
                        "subject": subject,
                        "score": evaluation["score"],
                        "layer_number": evaluation.get("layer_number"),
                    },
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
        painting_plan: PaintingPlan | None = None,
        current_layer: PlanLayer | None = None,
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
        if painting_plan and current_layer:
            layer_number = current_layer["layer_number"]
            layer_name = current_layer["name"]
            total_layers = painting_plan["total_layers"]

            layer_section = f"""

You are also evaluating progress on Layer {layer_number}: "{layer_name}".
The overall plan has {total_layers} layers.

Layer objectives:
- {current_layer["description"]}
- Expected palette: {", ".join(current_layer["colour_palette"])}
- Expected techniques: {current_layer["techniques"]}
"""

        prompt = f"""Current Canvas: [Image attached]
Subject: {subject}
Iteration: {iteration}{layer_section}

Task: Rate how well this image embodies {artist_name}'s artistic style on a scale of 0-100.

(See system instructions for evaluation criteria and response format.)"""

        return prompt

    def _build_static_evaluation_instructions(self, artist_name: str) -> str:
        """
        Build static evaluation instructions for caching.

        Returns the portion of the evaluation prompt that does not change
        between iterations: the role preamble, evaluation criteria, score
        rubric, JSON response schema, and output format instructions.
        These are intended to be sent as an Anthropic system prompt so they
        can be cached and reused across iterations.

        Args:
            artist_name (str): Target artist name for the evaluation

        Returns:
            str: Static evaluation instructions text
        """
        return f"""You are an art critic evaluating artwork for stylistic similarity to {artist_name}.

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
  "suggestions": "<areas that could be improved>"
}}

IMPORTANT: Respond ONLY with valid JSON. Do not include any text before or after the JSON object."""

    def _parse_evaluation_response(
        self,
        response_text: str,
        iteration: int,
        current_layer: PlanLayer | None = None,
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
        # Use shared robust JSON parsing utility
        try:
            data = clean_and_parse_json(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse evaluation JSON: {e}")
            logger.error(f"Response text (first 500 chars): {response_text[:500]}")
            raise ValueError(f"VLM returned invalid JSON: {e}") from e

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
