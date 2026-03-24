# QA Testing with Nova Act

## act() vs act_get()

- `act(prompt)` → `ActResult` — performs browser actions, raises on failure (no `succeeded` field — if it returns, it succeeded)
- `act_get(prompt, schema=)` → `ActGetResult` — performs actions AND extracts structured data

`ActGetResult` fields:
- `response` — raw string response
- `parsed_response` — JSON-parsed value matching the schema
- `valid_json` — whether the response was valid JSON
- `matches_schema` — whether the response matched the provided schema

`act_get` defaults to `STRING_SCHEMA` (`{"type": "string"}`) when no schema is provided.

## Schema Types

```python
from nova_act import NovaAct, BOOL_SCHEMA, STRING_SCHEMA

with NovaAct(starting_page="https://example.com") as nova:
    # Boolean — use BOOL_SCHEMA (exported from nova_act)
    is_visible = nova.act_get("Is the submit button visible?", schema=BOOL_SCHEMA)
    assert is_visible.parsed_response

    # String — act_get defaults to STRING_SCHEMA, but can be explicit
    title = nova.act_get("What is the page title?")
    assert "Dashboard" in title.response

    # Number — define inline (not exported from nova_act)
    price = nova.act_get("What is the product price?", schema={"type": "number"})
    assert price.parsed_response > 0

    # Integer
    count = nova.act_get("How many items are in the cart?", schema={"type": "integer"})
    assert count.parsed_response == 3
```

## Pydantic Schemas

```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    in_stock: bool

result = nova.act_get("Extract product name, price, and stock status", schema=Product.model_json_schema())
product = Product.model_validate(result.parsed_response)
assert product.price > 0
```

See `data_extraction.md` for more on `ActGetResult` fields and schema patterns.

## pytest Integration

### Fixtures
```python
import pytest
from nova_act import NovaAct

@pytest.fixture
def nova():
    with NovaAct(starting_page="https://example.com", headless=True) as n:
        yield n

@pytest.fixture
def authenticated_nova():
    """Pre-authenticated session (see authentication.md)."""
    with NovaAct(
        starting_page="https://example.com",
        user_data_dir="./test_sessions/authenticated",
        clone_user_data_dir=False,
        headless=True,
    ) as n:
        yield n
```

`headless=True` can also be set via the `NOVA_ACT_HEADLESS` environment variable.

### Parametrized Tests
```python
@pytest.mark.parametrize("query,expect_results", [
    ("laptop", True),
    ("xyznonexistent123", False),
])
def test_search(nova, query, expect_results):
    nova.act(f"enter '{query}' in the search box and press enter")
    has_results = nova.act_get("Are search results displayed?", schema=BOOL_SCHEMA)
    assert has_results.parsed_response == expect_results
```

### Error Handling
```python
from nova_act import ActAgentError, ActExecutionError

def test_with_error_handling(nova):
    try:
        nova.act("click the submit button")
    except ActAgentError:
        pytest.fail("Nova Act could not complete the action")
    except ActExecutionError:
        pytest.fail("Execution error occurred")
```

## unittest Integration

```python
import unittest
from nova_act import NovaAct

class TestLoginFlow(unittest.TestCase):
    def setUp(self):
        self.nova = NovaAct(starting_page="https://example.com", headless=True)
        self.nova.start()

    def tearDown(self):
        if self.nova:
            self.nova.stop()

    def test_successful_login(self):
        self.nova.act("click the login button")
        self.nova.act("enter 'user@example.com' in the email field")
        self.nova.act("click on the password field")
        self.nova.page.keyboard.type("password123")
        self.nova.act("click the submit button")

        logged_in = self.nova.act_get("Am I successfully logged in?", schema={"type": "boolean"})
        self.assertTrue(logged_in.parsed_response)
```

## Common Test Patterns

### Login Flow
```python
def test_login(nova):
    nova.act("click the login button")
    nova.act("enter 'user@example.com' in the email field")
    nova.act("click on the password field")
    nova.page.keyboard.type("secure_password")  # Playwright for sensitive input
    nova.act("click the submit button")

    logged_in = nova.act_get("Am I successfully logged in?", schema={"type": "boolean"})
    assert logged_in.parsed_response
```

### Form Validation
```python
def test_required_fields(nova):
    nova.act("navigate to the registration form")
    nova.act("click the submit button without filling any fields")

    errors = nova.act_get("Are validation errors displayed?", schema={"type": "boolean"})
    assert errors.parsed_response

    error_msg = nova.act_get("What error message is shown?", schema={"type": "string"})
    assert "required" in error_msg.response.lower()
```

### Search and Filter
```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float

class FilteredProducts(BaseModel):
    products: list[Product]

def test_price_filter(nova):
    nova.act("navigate to products and set price filter to max $100")
    nova.act("click apply filters")

    result = nova.act_get("Extract all visible products with prices", schema=FilteredProducts.model_json_schema())
    data = FilteredProducts.model_validate(result.parsed_response)
    for product in data.products:
        assert product.price <= 100, f"{product.name} exceeds filter"
```

### Navigation with Playwright
```python
def test_back_navigation(nova):
    nova.act("navigate to the products page")
    nova.act("click on the first product")

    on_detail = nova.act_get("Am I on a product detail page?", schema={"type": "boolean"})
    assert on_detail.parsed_response

    nova.page.go_back()  # Playwright navigation

    back_on_list = nova.act_get("Am I on the products listing page?", schema={"type": "boolean"})
    assert back_on_list.parsed_response
```

## NovaActTest Utility

For test suites with many assertions, wrap extraction and assertion helpers:

```python
from nova_act import NovaAct, BOOL_SCHEMA, STRING_SCHEMA

class NovaActTest(NovaAct):
    def extract_string(self, prompt: str) -> str:
        return self.act_get(prompt, schema=STRING_SCHEMA).response

    def extract_number(self, prompt: str) -> float:
        return self.act_get(prompt, schema={"type": "number"}).parsed_response

    def extract_boolean(self, prompt: str) -> bool:
        return self.act_get(prompt, schema=BOOL_SCHEMA).parsed_response

    def assert_true(self, prompt: str) -> None:
        assert self.extract_boolean(prompt), f"Expected true: {prompt}"

    def assert_contains(self, prompt: str, expected: str) -> None:
        val = self.extract_string(prompt)
        assert expected in val, f"Expected '{expected}' in '{val}'"
```

## Related Files
- `data_extraction.md` — Pydantic schemas, `ActGetResult` fields
- `playwright_interop.md` — Direct Playwright API usage alongside Nova Act
- `authentication.md` — Session persistence, auth patterns
