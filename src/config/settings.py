"""
settings.py
============
Resolves which environment is "active" for the current test run and
exposes a single `get_active_environment()` function that the rest of the
framework depends on.

Why this matters in an I. answer:
    Centralizing environment resolution means CI can simply set
    `TEST_ENV=staging` and nothing else in the codebase changes.
"""

import os

from src.config.environments import ENVIRONMENTS, EnvironmentConfig


def get_active_environment() -> EnvironmentConfig:
    """
    Return the EnvironmentConfig for the environment named in the
    TEST_ENV environment variable (defaults to "dev" if unset).

    Raises:
        ValueError: if TEST_ENV is set to an environment that doesn't
            exist in ENVIRONMENTS -- fails fast with a clear message
            rather than letting a typo silently fall back to dev.

    Returns:
        EnvironmentConfig: the resolved, immutable environment settings.
    """
    env_name = os.getenv("TEST_ENV", "dev").lower()

    if env_name not in ENVIRONMENTS:
        valid = ", ".join(ENVIRONMENTS.keys())
        raise ValueError(
            f"Unknown TEST_ENV '{env_name}'. Valid options are: {valid}"
        )

    return ENVIRONMENTS[env_name]
