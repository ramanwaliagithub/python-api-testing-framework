# python-api-testing-framework

A production-style Python API test automation framework for a P2P /
Invoice REST API, built with `requests` + `pytest`.

## Structure

```
src/
  config/        Environment config (dev/staging/prod) + active-env resolution
  api_clients/   BaseApiClient (HTTP plumbing) + AuthClient + InvoiceApiClient
  models/        Pydantic models (InvoiceResponse, InvoiceCreateRequest)
                 + raw JSON Schema for contract testing
  utils/         Logging config + test data factory
tests/
  conftest.py              Fixtures: env_config, auth_token, invoice_client, created_invoice_id
  test_invoice_api.py       CRUD + schema validation
  test_negative_scenarios.py  4xx/409/401 error-path coverage
  test_contract.py          JSON Schema contract tests
```

## Design principles demonstrated

- **Layered architecture**: tests -> domain client (InvoiceApiClient) -> base client (HTTP) -> requests.Session
- **Environment externalization**: `TEST_ENV=staging` switches base URL/timeouts with zero code change
- **Auth separation**: AuthClient is independent of business clients
- **Schema/contract validation**: Pydantic models + JSON Schema, not just status-code assertions
- **Test data factory**: avoids hardcoded/colliding data, supports parallel execution
- **Retry with backoff**: `tenacity` on the HTTP layer for transient network failures only (never on 4xx)

## Running

```bash
pip install -r requirements.txt
export TEST_ENV=dev
export API_CLIENT_ID=...
export API_CLIENT_SECRET=...

pytest -m smoke              # fast CI gate
pytest -m "regression"       # full suite
pytest -m contract           # contract tests only
pytest -n 4                  # explicit parallel sharding across 4 workers
```
