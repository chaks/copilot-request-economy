"""Test config loader module."""

import json
import tempfile
import os

from lib.config import load_config, DEFAULT_CONFIG


def test_load_config_file():
    """Verify config loader reads config.json."""
    config_path = tempfile.mktemp(suffix=".json")
    config_data = {"version": 2, "quota": {"monthlyLimit": 500}}
    with open(config_path, "w") as f:
        json.dump(config_data, f)

    config = load_config(config_path)
    assert config["quota"]["monthlyLimit"] == 500

    os.remove(config_path)


def test_config_defaults():
    """Verify default values when config missing."""
    missing_path = "/nonexistent/config.json"
    config = load_config(missing_path)

    assert config == DEFAULT_CONFIG


def test_invalid_json_returns_defaults():
    """Verify invalid JSON returns DEFAULT_CONFIG."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write("not valid json{{{")
        invalid_path = f.name

    config = load_config(invalid_path)
    assert config == DEFAULT_CONFIG

    os.remove(invalid_path)
