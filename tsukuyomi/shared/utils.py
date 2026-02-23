"""
Common utility functions for Tsukuyomi.

This module contains utility functions used across multiple systems.
"""

import uuid
from typing import Any, Dict, List, Optional


def generate_id() -> str:
    """Generate a unique identifier using UUID4.

    Returns:
        A unique UUID string.
    """
    return str(uuid.uuid4())


def to_pb_timestamp(t: float) -> Any:
    """Convert a float timestamp to protobuf Timestamp.

    Args:
        t: Unix timestamp as float.

    Returns:
        Protobuf Timestamp object.

    Note:
        This function dynamically imports protobuf to avoid hard dependencies.
        The actual protobuf module is imported when called.
    """
    try:
        from tsukuyomi.transport.proto import common_pb2

        seconds = int(t)
        nanos = int((t - seconds) * 1e9)
        return common_pb2.Timestamp(seconds=seconds, nanos=nanos)
    except ImportError:
        # Fallback if proto not available
        return {"seconds": int(t), "nanos": int((t - int(t)) * 1e9)}


def from_pb_timestamp(pb_timestamp: Any) -> float:
    """Convert protobuf Timestamp to float timestamp.

    Args:
        pb_timestamp: Protobuf Timestamp object.

    Returns:
        Unix timestamp as float.
    """
    return pb_timestamp.seconds + pb_timestamp.nanos / 1e9


def sanitize_input(text: str, max_length: int = 10000) -> str:
    """Sanitize user input to prevent injection attacks.

    Args:
        text: Input text to sanitize.
        max_length: Maximum allowed length.

    Returns:
        Sanitized text.
    """
    if not isinstance(text, str):
        raise ValueError("Input must be a string")

    # Truncate to max length
    text = text[:max_length]

    # Remove null bytes
    text = text.replace("\x00", "")

    return text.strip()


def validate_agent_id(agent_id: str) -> bool:
    """Validate agent ID format.

    Args:
        agent_id: Agent ID to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not agent_id or not isinstance(agent_id, str):
        return False
    return len(agent_id) > 0 and len(agent_id) <= 128


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split a list into chunks of specified size.

    Args:
        items: List to chunk.
        chunk_size: Size of each chunk.

    Returns:
        List of chunks.
    """
    return [items[i : i + chunk_size] for i in range(0, len(items), chunk_size)]


def safe_get(dictionary: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary.

    Args:
        dictionary: Dictionary to get value from.
        key: Key to look up.
        default: Default value if key not found.

    Returns:
        Value or default.
    """
    return dictionary.get(key, default)
