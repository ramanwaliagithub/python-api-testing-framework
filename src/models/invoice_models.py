"""
invoice_models.py
==================
Pydantic models representing the Invoice API's request/response shapes.

I. relevance
--------------------
"How do you validate that an API response matches its contract, not just
spot-check a couple of fields?" -- Pydantic (or jsonschema) model
validation is the answer: deserializing the response into a strongly
typed model fails loudly if a field is missing, has the wrong type, or
an enum value the API contract doesn't define.
"""


"""
Architecture
JSON Request
      |
      v
InvoiceCreateRequest
      |
      v
Invoice API
      |
      v
JSON Response
      |
      v
InvoiceResponse
      |
      v
Validation


Components:
InvoiceStatus: Enum of valid invoice states (PENDING_APPROVAL, APPROVED, REJECTED)
   |
   v     
LineItem: A single line item within an invoice (description, quantity, unit_price)
   |
   v  
InvoiceCreateRequest: Schema for POST /invoices body, with validation (e.g. currency must be uppercase)
   |
   v
InvoiceResponse: Schema for invoice GET/POST responses, matching the API contract


Tests
   |
   v
InvoiceApiClient
   |
   v
Response JSON
   |
   v
InvoiceResponse Model
   |
   v
Validation

Main Components:
InvoiceStatus (Enum)
LineItem (Nested Model)
InvoiceCreateRequest
(Request Validation)
InvoiceResponse
(Response Validation)
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class InvoiceStatus(str, Enum):
    """Valid invoice approval-workflow states."""
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class LineItem(BaseModel):
    """A single line item within an invoice."""
    description: str
    quantity: int = Field(gt=0, description="Must be a positive integer")
    unit_price: float = Field(ge=0, description="Must not be negative")


class InvoiceCreateRequest(BaseModel):
    """
    Request body schema for POST /invoices.

    Using a Pydantic model for the *request* (not just the response)
    means malformed test data is caught at construction time, before a
    single HTTP call is made -- shifting failures left.
    """
    vendor_id: str
    amount: float = Field(gt=0)
    currency: str = Field(min_length=3, max_length=3)
    line_items: list[LineItem]

    @field_validator("currency")
    @classmethod
    def currency_must_be_uppercase(cls, value: str) -> str:
        """Enforce ISO-4217 style uppercase currency codes, e.g. 'INR'."""
        if not value.isupper():
            raise ValueError("currency code must be uppercase, e.g. 'INR'")
        return value


class InvoiceResponse(BaseModel):
    """
    Response body schema for invoice GET/POST endpoints.

    Calling `InvoiceResponse.model_validate(response.json())` in a test
    is itself a contract-validation assertion -- if the API silently
    renames or drops a field, this raises a ValidationError and fails
    the test with a precise diff.
    """
    id: str
    vendor_id: str
    amount: float
    currency: str
    status: InvoiceStatus
    line_items: list[LineItem]
    created_at: datetime
    updated_at: datetime
