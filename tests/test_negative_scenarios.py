"""
test_negative_scenarios.py
============================
Negative / error-path test coverage -- a category I.ers often
specifically ask about ("walk me through your negative testing
strategy for an API").
"""

import pytest

from src.utils.test_data_factory import (
    build_invoice_payload_missing_required_field,
    build_invoice_payload_with_negative_amount,
)


@pytest.mark.negative
class TestInvoiceNegativeScenarios:
    """Each test asserts the API fails *safely* and *informatively*."""

    @pytest.mark.parametrize(
        "missing_field", ["vendor_id", "amount", "currency", "line_items"]
    )
    def test_create_invoice_missing_required_field_returns_400(
        self, invoice_client, missing_field
    ):
        """
        Removing any single required field should yield 400, never a
        500 -- a 500 here would indicate the API isn't validating input
        and is instead crashing on a null/missing value internally.
        """
        payload = build_invoice_payload_missing_required_field(missing_field)

        response = invoice_client.create_invoice(payload)

        assert response.status_code == 400, (
            f"Expected 400 for missing '{missing_field}', got "
            f"{response.status_code}: {response.text}"
        )
        assert missing_field in response.text.lower() or "required" in response.text.lower()

    def test_create_invoice_with_negative_amount_returns_400(self, invoice_client):
        """Business-rule validation: amount must be positive."""
        payload = build_invoice_payload_with_negative_amount()

        response = invoice_client.create_invoice(payload)

        assert response.status_code == 400

    def test_invalid_status_transition_returns_409_conflict(
        self, invoice_client, created_invoice_id
    ):
        """
        Approving an invoice that's already REJECTED should be a 409
        Conflict (invalid state transition), not silently accepted.
        """
        invoice_client.update_invoice_status(created_invoice_id, "REJECTED")

        response = invoice_client.update_invoice_status(created_invoice_id, "APPROVED")

        assert response.status_code == 409

    def test_unauthenticated_request_returns_401(self, env_config):
        """A request with no/invalid bearer token must be rejected with 401."""
        from src.api_clients.invoice_client import InvoiceApiClient

        unauthenticated_client = InvoiceApiClient(env_config, auth_token=None)

        response = unauthenticated_client.list_invoices()

        assert response.status_code == 401
