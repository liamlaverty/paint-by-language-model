"""Evaluation VLM Client for assessing artistic style similarity."""

import json
import logging
import re
from datetime import datetime

from config import LMSTUDIO_BASE_URL, VLM_MODEL, VLM_TIMEOUT
from lmstudio_client import LMStudioClient
from models.evaluation_result import EvaluationResult

logger = logging.getLogger(__name__)


class EvaluationVLMClient:
    """Client for querying VLMs to evaluate artistic style."""

    def __init__(
        self, base_url: str = LMSTUDIO_BASE_URL, model: str = VLM_MODEL, timeout: int = VLM_TIMEOUT
    ):
        """
        Initialize Evaluation VLM Client.

        Args:
            base_url (str): LMStudio server URL
            model (str): VLM model identifier
            timeout (int): Request timeout in seconds
        """
        self.lmstudio_client = LMStudioClient(base_url=base_url, model=model, timeout=timeout)
        self.model = model
        self.timeout = timeout
        logger.info(f"Initialized EvaluationVLMClient with model: {model}")

    def evaluate_style(
        self, canvas_image: bytes, artist_name: str, subject: str, iteration: int
    ) -> EvaluationResult:
        """
        Evaluate canvas style similarity to target artist.

        Args:
            canvas_image (bytes): Current canvas as image bytes
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number

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
            artist_name=artist_name, subject=subject, iteration=iteration
        )

        # Query VLM
        try:
            response_text = self.lmstudio_client.query_multimodal(
                prompt=prompt, image_bytes=canvas_image
            )

            # Parse response
            evaluation = self._parse_evaluation_response(
                response_text=response_text, iteration=iteration
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

    def _build_evaluation_prompt(self, artist_name: str, subject: str, iteration: int) -> str:
        """
        Build prompt for style evaluation.

        Args:
            artist_name (str): Target artist name
            subject (str): Subject being painted
            iteration (int): Current iteration number

        Returns:
            str: Formatted prompt
        """
        prompt = f"""You are an art critic evaluating artwork for stylistic similarity to {artist_name}.

Current Canvas: [Image attached]
Subject: {subject}
Iteration: {iteration}

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
  "suggestions": "<areas that could be improved>"
}}

IMPORTANT: Respond ONLY with valid JSON. Do not include any text before or after the JSON object."""

        return prompt

    def _parse_evaluation_response(self, response_text: str, iteration: int) -> EvaluationResult:
        """
        Parse VLM evaluation response into EvaluationResult.

        Args:
            response_text (str): Raw VLM response
            iteration (int): Current iteration number

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

        return result
