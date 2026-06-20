"""
auth_client.py
==============
Handles OAuth2 client-credentials token acquisition, separate from the
business API clients.

I. relevance
--------------------
Separating auth from business logic clients is a common "framework
design" I. talking point: it lets you swap auth strategies
(OAuth2, API key, mTLS) without touching InvoiceApiClient at all.
"""


"""
AuthClient is a dedicated authentication service class that obtains 
and caches OAuth2 access tokens using the Client Credentials Grant flow.

Instead of requesting a new token for every API call, it:
Fetches a token once.
Caches it.
Tracks its expiry time.
Automatically refreshes it before expiration.
Returns a valid token whenever business clients need one.

This follows the Separation of Concerns principle because authentication 
logic is isolated from API/business logic.

Architecture Diagram
+----------------+
| InvoiceClient  |
+----------------+
        |
        v
+----------------+
|  AuthClient    |
+----------------+
        |
        v
 OAuth Token API

Flow
get_token()
    |
    |
    |-- Cached token exists?
    |       |
    |       NO
    |       |
    |   Fetch new token
    |
    YES
    |
    Token expired?
    |
    YES --> Fetch new token
    |
    NO --> Return cached token

"""
import logging
import time

import requests

from src.config.environments import EnvironmentConfig

logger = logging.getLogger(__name__)


class AuthClient:
    """
    Obtains and caches OAuth2 bearer tokens via the client-credentials
    grant, refreshing automatically once the cached token is close to
    expiry.
    """

    # Refresh 30s before actual expiry to avoid using a token that
    # expires mid-request (clock skew safety margin).
    _EXPIRY_SAFETY_MARGIN_SECONDS = 30

    def __init__(self, env_config: EnvironmentConfig, client_id: str, client_secret: str):
        """
        Args:
            env_config: Environment settings containing the auth_url.
            client_id: OAuth2 client id (from a secrets manager / env var
                in real CI -- never hardcoded).
            client_secret: OAuth2 client secret.
        """
        self.env_config = env_config
        self.client_id = client_id
        self.client_secret = client_secret
        self._cached_token: str | None = None
        self._token_expiry_epoch: float = 0.0

    def get_token(self) -> str:
        """
        Return a valid bearer token, fetching a new one only if the
        cached token is missing or about to expire.

        Returns:
            str: a valid OAuth2 access token.

        Raises:
            RuntimeError: if the token endpoint returns a non-200 response.
        """
        if self._cached_token and time.time() < self._token_expiry_epoch:
            return self._cached_token

        return self._fetch_new_token()

    def _fetch_new_token(self) -> str:
        """Call the token endpoint and cache the result with its expiry."""
        response = requests.post(
            self.env_config.auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
            },
            timeout=self.env_config.timeout_seconds,
            verify=self.env_config.verify_ssl,
        )

        if response.status_code != 200:
            logger.error("Token request failed: %s", response.text)
            raise RuntimeError(
                f"Failed to obtain auth token, status={response.status_code}"
            )

        body = response.json()
        self._cached_token = body["access_token"]
        expires_in = body.get("expires_in", 3600)
        self._token_expiry_epoch = (
            time.time() + expires_in - self._EXPIRY_SAFETY_MARGIN_SECONDS
        )

        logger.info("Fetched new auth token, expires_in=%ss", expires_in)
        return self._cached_token
