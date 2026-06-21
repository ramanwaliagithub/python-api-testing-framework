"""
schemas.py
==========
Raw JSON Schema definitions, used with the `jsonschema` library for
contract testing -- an alternative/complement to Pydantic model
validation.

I. relevance
--------------------
Architect-level I.s often ask: "How would you implement
consumer-driven contract testing without adopting a full Pact setup?"
A lightweight first step is storing the agreed JSON Schema (the
"contract") in version control and validating every response against it
in CI -- catching breaking API changes before they reach consumers.
"""


"""
Architecture
Provider API
      |
      v
JSON Response
      |
      v
JSON Schema
      |
      v
Validation
      |
      v
Pass / Fail



EnvironmentConfig
        |
AuthClient
        |
BaseApiClient
        |
InvoiceApiClient
        |
Response JSON
        |
--------------------
|                  |
v                  v
Pydantic      JSON Schema
Validation    Validation

"""


INVOICE_RESPONSE_SCHEMA: dict = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "InvoiceResponse",
    "type": "object",
    "required": ["id", "vendor_id", "amount", "currency", "status", "line_items"],
    "properties": {
        "id": {"type": "string"},
        "vendor_id": {"type": "string"},
        "amount": {"type": "number", "minimum": 0},
        "currency": {"type": "string", "minLength": 3, "maxLength": 3},
        "status": {
            "type": "string",
            "enum": ["PENDING_APPROVAL", "APPROVED", "REJECTED"],
        },
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["description", "quantity", "unit_price"],
                "properties": {
                    "description": {"type": "string"},
                    "quantity": {"type": "integer", "minimum": 1},
                    "unit_price": {"type": "number", "minimum": 0},
                },
            },
        },
    },
    "additionalProperties": True,
}
