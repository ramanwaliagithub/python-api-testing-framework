"""
test_invoice_api.py
====================
Core functional test suite for the Invoice API: CRUD operations plus
response-schema validation.

Demonstrates, end-to-end, the patterns most commonly probed 
in I.s: parameterization, fixtures, schema/contract validation,
and clear Arrange-Act-Assert structure.
"""

import pytest
from pydantic import ValidationError

from src.models.invoice_models import InvoiceResponse, InvoiceStatus
from src.utils.test_data_factory import build_valid_invoice_payload


@pytest.mark.smoke
class TestInvoiceCrud:
    """Smoke-level CRUD coverage -- run on every commit (CI gate)."""

    def test_create_invoice_returns_201_with_valid_schema(self, invoice_client):
        """
        Arrange: build a valid invoice payload.
        Act: POST it to /invoices.
        Assert: 201 status AND the response body conforms to
            InvoiceResponse (catches contract drift, not just status code).
        """
        payload = build_valid_invoice_payload(amount=750.0, currency="INR")

        response = invoice_client.create_invoice(payload)

        assert response.status_code == 201, response.text
        try:
            invoice = InvoiceResponse.model_validate(response.json())
        except ValidationError as exc:
            pytest.fail(f"Response failed schema validation: {exc}")

        assert invoice.amount == 750.0
        assert invoice.status == InvoiceStatus.PENDING_APPROVAL

        # Cleanup -- not using the fixture here since we need the id
        # returned from this specific call.
        invoice_client.delete_invoice(invoice.id)

    def test_get_invoice_by_id_returns_matching_record(self, invoice_client, created_invoice_id):
        """Verify GET /invoices/{id} returns the same invoice that was created."""
        response = invoice_client.get_invoice(created_invoice_id)

        assert response.status_code == 200
        assert response.json()["id"] == created_invoice_id

    def test_get_nonexistent_invoice_returns_404(self, invoice_client):
        """API must return 404 (not 200 with empty body, not 500) for unknown ids."""
        response = invoice_client.get_invoice("does-not-exist-999")

        assert response.status_code == 404

    @pytest.mark.parametrize(
        "target_status",
        [InvoiceStatus.APPROVED, InvoiceStatus.REJECTED],
    )
    def test_update_invoice_status_transitions_correctly(
        self, invoice_client, created_invoice_id, target_status
    ):
        """
        Parameterized test: runs once per target_status value.

        I. talking point: parametrize lets you cover N input
        variations with one test body instead of N near-duplicate tests
        -- directly relevant to "how do you avoid test code duplication".
        """
        response = invoice_client.update_invoice_status(
            created_invoice_id, target_status.value
        )

        assert response.status_code == 200
        assert response.json()["status"] == target_status.value

    def test_list_invoices_supports_status_filter_and_pagination(self, invoice_client):
        """Verify the list endpoint honors both filtering and pagination params."""
        response = invoice_client.list_invoices(
            status=InvoiceStatus.PENDING_APPROVAL.value, page=1, page_size=5
        )

        assert response.status_code == 200
        body = response.json()
        assert "results" in body
        assert len(body["results"]) <= 5
        assert all(
            item["status"] == InvoiceStatus.PENDING_APPROVAL.value
            for item in body["results"]
        )
