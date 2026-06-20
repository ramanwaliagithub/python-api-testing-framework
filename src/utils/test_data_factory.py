"""
test_data_factory.py
=====================
Factory functions that generate valid (and intentionally invalid) test
data, rather than hardcoding payloads inline in every test.

I. relevance
--------------------
"How do you keep test data maintainable across a large suite?" -- the
Test Data Factory pattern: one place to change when the API contract
changes, and a place to generate *unique* data per test run to avoid
collisions (e.g. duplicate vendor IDs) when tests run in parallel.
"""

import uuid


def build_valid_invoice_payload(amount: float = 500.0, currency: str = "INR") -> dict:
    """
    Build a syntactically and semantically valid invoice creation
    payload, with a unique vendor_id so parallel test runs (pytest-xdist)
    never collide on the same data.

    Args:
        amount: Total invoice amount.
        currency: ISO currency code.

    Returns:
        dict: ready to pass as `json=` to InvoiceApiClient.create_invoice.
    """
    return {
        "vendor_id": f"V-{uuid.uuid4().hex[:8]}",
        "amount": amount,
        "currency": currency,
        "line_items": [
            {"description": "Consulting services", "quantity": 1, "unit_price": amount}
        ],
    }


def build_invoice_payload_missing_required_field(field_to_remove: str) -> dict:
    """
    Build an otherwise-valid payload with one required field removed --
    used to drive negative test cases (expecting a 400 Bad Request).

    Args:
        field_to_remove: Key to strip out of the payload, e.g. "vendor_id".

    Returns:
        dict: invalid payload missing `field_to_remove`.
    """
    payload = build_valid_invoice_payload()
    payload.pop(field_to_remove, None)
    return payload


def build_invoice_payload_with_negative_amount() -> dict:
    """
    Build a payload with a negative amount -- used to verify the API
    rejects business-rule violations, not just structurally-invalid JSON.

    Returns:
        dict: payload with amount=-100 (should trigger a 400/422).
    """
    payload = build_valid_invoice_payload()
    payload["amount"] = -100.0
    return payload
