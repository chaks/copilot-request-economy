"""Configuration loader."""

import copy
import json
from typing import Any


DEFAULT_CONFIG = {
    "version": 2,
    "quota": {"monthlyLimit": 300, "resetDate": 1, "warningThreshold": 50},
}


def load_config(path: str) -> dict[str, Any]:
    """Load configuration from JSON file.

    Returns DEFAULT_CONFIG if file doesn't exist or is invalid.
    """
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return copy.deepcopy(DEFAULT_CONFIG)
