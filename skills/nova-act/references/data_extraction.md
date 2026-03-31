# Data Extraction

Extract structured data from web pages using `act_get()` with JSON Schema.

## Core Pattern

```python
from pydantic import BaseModel
from nova_act import NovaAct

class Product(BaseModel):
    name: str
    price: float
    in_stock: bool

with NovaAct(starting_page="https://example.com") as nova:
    result = nova.act_get(
        "Extract the product information from this page",
        schema=Product.model_json_schema()
    )
    product = Product.model_validate(result.parsed_response)
```

## ActGetResult Fields

- `result.response` — raw string response from the model
- `result.parsed_response` — parsed JSON matching the schema (use this for Pydantic validation)
- `result.valid_json` — whether the response was valid JSON
- `result.matches_schema` — whether the parsed response matches the provided schema

## Schema Options

Pass any JSON Schema dict to `schema=`. Defaults to `{"type": "string"}` if omitted.

```python
# Inline schema (no Pydantic needed)
result = nova.act_get("How many items?", schema={"type": "integer"})

# Boolean check
result = nova.act_get("Is the user logged in?", schema={"type": "boolean"})

# List extraction with Pydantic
class SearchResult(BaseModel):
    title: str
    url: str

class SearchResults(BaseModel):
    results: list[SearchResult]

result = nova.act_get("Extract all search results", schema=SearchResults.model_json_schema())
```

See `playwright_interop.md` for combining Nova Act with direct Playwright APIs.
