"""
test_contract.py
=================
Contract testing example using raw JSON Schema (`jsonschema` library) --
a lightweight alternative to a full Pact consumer-driven-contract setup,
often the right answer when asked "how would you add contract testing
without a big new tool investment".
"""

"""
Functional Test
      |
      v
Did API do the right thing?

Contract Test
      |
      v
Did API return data in the agreed format?

Architecture
Backend API
      |
      v
JSON Response
      |
      v
JSON Schema
      |
      v
Contract Validation
      |
      v
PASS / FAIL
"""

import pytest
from jsonschema import ValidationError, validate

from src.models.schemas import INVOICE_RESPONSE_SCHEMA
from src.utils.test_data_factory import build_valid_invoice_payload


@pytest.mark.contract
class TestInvoiceContract:
    """
    These tests fail whenever the API's response shape drifts from the
    agreed contract -- e.g. a backend change renames `unit_price` to
    `price`, or adds an invoice status value the schema doesn't expect.
    This is exactly the kind of test that should sit in a CI/CD
    "contract gate" stage, run against every backend PR before merge.
    """

    def test_invoice_response_matches_agreed_json_schema(self, invoice_client):
        payload = build_valid_invoice_payload()
        response = invoice_client.create_invoice(payload)
        body = response.json()

        try:
            validate(instance=body, schema=INVOICE_RESPONSE_SCHEMA)
        except ValidationError as exc:
            pytest.fail(f"Contract violation: {exc.message}")

        invoice_client.delete_invoice(body["id"])

    def test_invoice_status_enum_matches_contract(self, invoice_client):
        """
        Explicitly checks the API never returns a status value outside
        the three the contract defines -- guards against the backend
        silently introducing a new workflow state that consumers
        (downstream UI, reporting) don't know how to render.
        """
        response = invoice_client.list_invoices(page_size=50)
        body = response.json()

        allowed_statuses = set(
            INVOICE_RESPONSE_SCHEMA["properties"]["status"]["enum"]
        )
        returned_statuses = {item["status"] for item in body["results"]}

        unexpected = returned_statuses - allowed_statuses
        assert not unexpected, f"API returned undocumented status values: {unexpected}"
