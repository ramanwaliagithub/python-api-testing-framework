"""
environments.py
================
Defines per-environment configuration (base URLs, timeouts, auth endpoints)
for the API test framework.

I. relevance
--------------------
A very common architect-level question is:
    "How do you run the same test suite against dev / staging / prod
     without duplicating test code?"

The answer demonstrated here: externalize everything environment-specific
into a single dictionary keyed by environment name, and resolve the active
environment once (via an env var) at runtime. Tests never hardcode a URL.
"""

"""
Architecture
Tests
  |
  v
InvoiceApiClient
  |
  v
EnvironmentConfig
  |
  v
ENVIRONMENTS
  |
  +---- DEV
  +---- STAGING
  +---- PROD


Dataclass Automatically creates: __init__()
__repr__()
__eq__()
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EnvironmentConfig:
    """
    Immutable value object describing a single environment's settings.

    Attributes:
        name: Logical environment name (dev/staging/prod).
        base_url: Root URL for the Invoice/P2P API under test.
        auth_url: Token endpoint used to obtain a bearer token.
        timeout_seconds: Default per-request timeout.
        verify_ssl: Whether to validate TLS certs (False only for local/dev).
    """
    name: str
    base_url: str
    auth_url: str
    timeout_seconds: int = 10
    verify_ssl: bool = True


# Real-world pattern: one source of truth for all environments.
# In CI/CD this would typically be populated from environment variables /
# a secrets manager rather than hardcoded -- shown here in plain form for
# clarity.
ENVIRONMENTS: dict[str, EnvironmentConfig] = {
    "dev": EnvironmentConfig(
        name="dev",
        base_url="https://api-dev.p2p-invoicing.example.com/v1",
        auth_url="https://auth-dev.p2p-invoicing.example.com/oauth/token",
        timeout_seconds=15,
        verify_ssl=False,
    ),
    "staging": EnvironmentConfig(
        name="staging",
        base_url="https://api-staging.p2p-invoicing.example.com/v1",
        auth_url="https://auth-staging.p2p-invoicing.example.com/oauth/token",
        timeout_seconds=10,
        verify_ssl=True,
    ),
    "prod": EnvironmentConfig(
        name="prod",
        base_url="https://api.p2p-invoicing.example.com/v1",
        auth_url="https://auth.p2p-invoicing.example.com/oauth/token",
        timeout_seconds=10,
        verify_ssl=True,
    ),
}
