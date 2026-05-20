# Pytest patterns for Python TDD

Use these examples only when the project has no stronger local convention.

## Test naming

Prefer behavior names:

```python
def test_quote_total_applies_bulk_discount():
    ...
```

Avoid names that reveal implementation details:

```python
# Poor: asserts private method choreography instead of behavior.
def test_quote_total_calls_discount_service():
    ...
```

## Arrange-Act-Assert

```python
def test_quote_total_applies_bulk_discount():
    cart = Cart([LineItem("sku-1", quantity=10, unit_price=Decimal("12.00"))])

    total = quote_total(cart)

    assert total == Decimal("108.00")
```

## Parametrized examples

```python
import pytest

@pytest.mark.parametrize(
    ("quantity", "expected"),
    [
        (0, Decimal("0.00")),
        (1, Decimal("12.00")),
        (10, Decimal("108.00")),
    ],
)
def test_quote_total_handles_quantity_boundaries(quantity, expected):
    cart = Cart([LineItem("sku-1", quantity=quantity, unit_price=Decimal("12.00"))])

    assert quote_total(cart) == expected
```

Use parametrization when cases share the same behavior. Split into separate tests when the reason for failure would be ambiguous.

## Exceptions

```python
import pytest


def test_create_user_rejects_empty_email():
    with pytest.raises(ValidationError, match="email"):
        create_user(email="")
```

## Filesystem isolation

```python
def test_loader_reads_config_from_given_path(tmp_path):
    config_path = tmp_path / "config.toml"
    config_path.write_text("enabled = true\n")

    config = load_config(config_path)

    assert config.enabled is True
```

## Environment isolation

```python
def test_api_client_reads_timeout_from_environment(monkeypatch):
    monkeypatch.setenv("API_TIMEOUT_SECONDS", "3")

    client = build_client_from_env()

    assert client.timeout_seconds == 3
```

## Mocking and fakes

Prefer fakes for domain boundaries and mocks for narrow interaction contracts.

```python
class FakeEmailSender:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


def test_signup_sends_welcome_email():
    sender = FakeEmailSender()

    signup(email="a@example.com", sender=sender)

    assert len(sender.sent) == 1
    assert sender.sent[0].recipient == "a@example.com"
```

Patch where the object is used, not where it is defined.

## Async code

Use the project's existing async test plugin. If `pytest-asyncio` is configured:

```python
import pytest

@pytest.mark.asyncio
async def test_repository_fetches_user_by_id():
    repo = UserRepository(fake_pool)

    user = await repo.get("user-1")

    assert user.id == "user-1"
```

## Property-style tests

Use property-based tests only when Hypothesis or an equivalent tool is already configured. Good candidates are parsers, serialization round trips, normalization, sorting, idempotence, and numeric invariants.

## Regression tests

For bugs, encode the failure before the fix:

```python
def test_parser_preserves_quoted_commas_regression():
    row = parse_csv_line('"last, first",42')

    assert row == ["last, first", "42"]
```

Keep the test name clear enough to prevent future removal as "redundant".
