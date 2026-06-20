"""
conftest.py
===========
Shared pytest fixtures: environment resolution, auth token, and the
InvoiceApiClient instance every test depends on.

I. relevance
--------------------
"How do you manage test setup/teardown and dependency injection in
pytest?" -- fixtures are pytest's answer to JUnit's @Before/@After and
TestNG's @BeforeClass: declarative, composable, and scoped (function/
class/module/session) so expensive setup (like auth) happens once per
session, not once per test.
"""

import os

import pytest

from src.api_clients.auth_client import AuthClient
from src.api_clients.invoice_client import InvoiceApiClient
from src.config.settings import get_active_environment
from src.utils.logger import configure_logging

configure_logging()


@pytest.fixture(scope="session")
def env_config():
    """
    Session-scoped: resolved once per test run based on the TEST_ENV
    environment variable (see src/config/settings.py).
    """
    return get_active_environment()


@pytest.fixture(scope="session")
def auth_token(env_config) -> str:
    """
    Session-scoped: fetch the OAuth2 token ONCE per test session and
    reuse it across all tests, instead of re-authenticating per test
    (which would be slow and could hit auth-server rate limits).
    """
    client_id = os.getenv("API_CLIENT_ID", "test-client-id")
    client_secret = os.getenv("API_CLIENT_SECRET", "test-client-secret")
    auth_client = AuthClient(env_config, client_id, client_secret)
    return auth_client.get_token()


@pytest.fixture()
def invoice_client(env_config, auth_token) -> InvoiceApiClient:
    """
    Function-scoped: a fresh InvoiceApiClient per test. Function scope
    (not session scope) avoids one test's session state (e.g. custom
    headers) leaking into another.
    """
    return InvoiceApiClient(env_config, auth_token=auth_token)


@pytest.fixture()
def created_invoice_id(invoice_client):
    """
    Creates an invoice before the test runs and deletes it afterward --
    a teardown pattern that keeps the API's test data clean regardless
    of whether the test passes or fails (the `yield` splits setup/teardown).
    """
    from src.utils.test_data_factory import build_valid_invoice_payload

    response = invoice_client.create_invoice(build_valid_invoice_payload())
    invoice_id = response.json()["id"]

    yield invoice_id

    # Teardown -- runs even if the test itself fails/raises.
    invoice_client.delete_invoice(invoice_id)
