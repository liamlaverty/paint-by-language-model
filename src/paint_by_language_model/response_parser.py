"""Parse and structure LLM responses about artists."""

from datetime import datetime
from typing import TypedDict


class ArtistAnalysis(TypedDict):
    """Structure for artist analysis data."""

    artist_name: str
    query_timestamp: str
    response: str
    model_used: str


def parse_response(
    artist_name: str,
    llm_response: str,
    model_name: str,
) -> ArtistAnalysis:
    """
    Parse an LLM response into a structured format.

    Args:
        artist_name (str): Name of the artist queried
        llm_response (str): Raw response text from the LLM
        model_name (str): Name of the model used

    Returns:
        (ArtistAnalysis): Structured artist analysis dictionary
    """
    return ArtistAnalysis(
        artist_name=artist_name,
        query_timestamp=datetime.now().isoformat(),
        response=llm_response,
        model_used=model_name,
    )
