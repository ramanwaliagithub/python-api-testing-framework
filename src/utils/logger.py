"""
logger.py
=========
Single place to configure logging for the whole framework so that every
module's logs (request/response, retries, fixture setup/teardown) share
a consistent format -- essential for debugging flaky tests in CI logs.
"""

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure root logging once per test run.

    Args:
        level: Logging verbosity, e.g. logging.DEBUG for deep
            troubleshooting of a flaky test, logging.INFO for normal CI runs.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
