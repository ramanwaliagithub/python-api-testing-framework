"""
invoice_client.py
==================
Domain-specific client for the Invoice / P2P API. This is the layer test
code actually talks to -- it exposes business-meaningful methods instead
of raw HTTP verbs, and is the direct analogue of the "Page Object" pattern
in UI automation (sometimes called a "Service Object" or "API Object" in
API testing).
"""

"""
InvoiceApiClient is a domain-specific API client
 (also called a Service Object or API Object).

Architecture:
Tests
  |
  v
InvoiceApiClient
  |
  v
BaseApiClient
  |
  v
requests.Session
  |
  v
Invoice API


Responsibility of each layer

Tests -> Business validation

InvoiceApiClient -> Business operations

BaseApiClient -> HTTP plumbing

requests -> Network communication
"""

from requests import Response

from src.api_clients.base_client import BaseApiClient


class InvoiceApiClient(BaseApiClient):
    """
    Encapsulates every operation the Invoice API exposes. Test code
    should never construct raw URLs/payloads itself -- it calls these
    methods and asserts on the returned Response.
    """

    RESOURCE_PATH = "/invoices"

    def create_invoice(self, payload: dict) -> Response:
        """
        Create a new invoice.

        Args:
            payload: Invoice creation body, e.g.
                {"vendor_id": "V-100", "amount": 250.0, "currency": "INR",
                 "line_items": [...]}.

        Returns:
            Response: expected 201 Created with the new invoice (incl. id)
                in the body on success.
        """
        return self.post(self.RESOURCE_PATH, json=payload)

    def get_invoice(self, invoice_id: str) -> Response:
        """
        Fetch a single invoice by id.

        Args:
            invoice_id: The invoice's unique identifier.

        Returns:
            Response: 200 with invoice body, or 404 if it doesn't exist.
        """
        return self.get(f"{self.RESOURCE_PATH}/{invoice_id}")

    def list_invoices(self, status: str | None = None, page: int = 1, page_size: int = 20) -> Response:
        """
        List invoices, optionally filtered by approval status.

        Args:
            status: Optional filter, e.g. "PENDING_APPROVAL", "APPROVED", "REJECTED".
            page: 1-indexed page number.
            page_size: Number of records per page.

        Returns:
            Response: 200 with a paginated list payload.
        """
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        return self.get(self.RESOURCE_PATH, params=params)

    def update_invoice_status(self, invoice_id: str, new_status: str) -> Response:
        """
        Transition an invoice's approval status (e.g. approve/reject).

        Args:
            invoice_id: Target invoice id.
            new_status: One of "APPROVED", "REJECTED", "PENDING_APPROVAL".

        Returns:
            Response: 200 on success, 409 if the transition is invalid
                (e.g. approving an already-rejected invoice).
        """
        return self.put(
            f"{self.RESOURCE_PATH}/{invoice_id}/status",
            json={"status": new_status},
        )

    def delete_invoice(self, invoice_id: str) -> Response:
        """
        Delete (or soft-delete, depending on API contract) an invoice.

        Args:
            invoice_id: Target invoice id.

        Returns:
            Response: 204 No Content on success.
        """
        return self.delete(f"{self.RESOURCE_PATH}/{invoice_id}")
