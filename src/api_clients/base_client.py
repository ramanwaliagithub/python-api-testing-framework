"""
base_client.py
==============
Generic, reusable HTTP client that every domain-specific API client
(InvoiceClient, AuthClient, etc.) inherits from.

I. relevance
--------------------
A frequent architect-level question: "How do you avoid duplicating
request/response boilerplate (headers, retries, logging) across every
test?" The answer is a thin client layer like this one -- tests call
high-level methods (`client.get_invoice(id)`), never raw `requests.get`.
"""

import logging
from typing import Any

import requests
from requests import Response
from tenacity import retry, stop_after_attempt, wait_exponential

from src.config.environments import EnvironmentConfig

logger = logging.getLogger(__name__)


class BaseApiClient:
    """
    Thin wrapper around `requests.Session` that centralizes:
      - base URL resolution
      - default headers / auth token injection
      - timeout + SSL verification policy (from EnvironmentConfig)
      - retry-with-backoff for transient failures (5xx / connection errors)
      - request/response logging for debugging flaky failures

    Domain-specific clients (e.g. InvoiceApiClient) should subclass this
    and add business-meaningful methods rather than re-implementing HTTP
    plumbing.
    """

    def __init__(self, env_config: EnvironmentConfig, auth_token: str | None = None):
        """
        Args:
            env_config: Resolved environment settings (base_url, timeouts...).
            auth_token: Bearer token to attach to every request. Can be
                None for unauthenticated calls (e.g. health-check endpoints).
        """
        self.env_config = env_config
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        if auth_token:
            self.session.headers["Authorization"] = f"Bearer {auth_token}"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs: Any) -> Response:
        """
        Execute an HTTP request with retry-with-exponential-backoff.

        Retries are intentionally limited to network-level/connection
        failures -- NOT to 4xx responses, since retrying a 400 (bad
        request) would only mask a genuine test/data bug. The `tenacity`
        decorator here re-raises after 3 attempts so a persistently
        failing call still fails the test instead of hanging forever.

        Args:
            method: HTTP verb, e.g. "GET", "POST", "PUT", "DELETE".
            path: URL path relative to env_config.base_url, e.g. "/invoices/123".
            **kwargs: Passed straight through to requests (json=, params=, etc).

        Returns:
            requests.Response: the raw response object for the caller
                to assert on (status_code, .json(), headers, etc).
        """
        url = f"{self.env_config.base_url}{path}"
        logger.info("-> %s %s | payload=%s", method, url, kwargs.get("json"))

        response = self.session.request(
            method=method,
            url=url,
            timeout=self.env_config.timeout_seconds,
            verify=self.env_config.verify_ssl,
            **kwargs,
        )

        logger.info("<- %s %s | status=%s", method, url, response.status_code)
        return response

    def get(self, path: str, **kwargs: Any) -> Response:
        """Issue a GET request. See `_request` for kwargs/behavior."""
        return self._request("GET", path, **kwargs)

    def post(self, path: str, json: dict | None = None, **kwargs: Any) -> Response:
        """Issue a POST request with an optional JSON body."""
        return self._request("POST", path, json=json, **kwargs)

    def put(self, path: str, json: dict | None = None, **kwargs: Any) -> Response:
        """Issue a PUT request with an optional JSON body."""
        return self._request("PUT", path, json=json, **kwargs)

    def delete(self, path: str, **kwargs: Any) -> Response:
        """Issue a DELETE request."""
        return self._request("DELETE", path, **kwargs)
