# Playwright Interop

`nova.page` exposes the underlying Playwright `Page` object for direct browser control alongside Nova Act.

## Access

```python
with NovaAct(starting_page="https://example.com") as nova:
    page = nova.page          # current page (Playwright Page)
    all_pages = nova.pages    # all open pages
    page_2 = nova.get_page(1) # specific page by index
```

## When to Use Playwright Directly

- **Sensitive input** — passwords, credit cards, SSNs (avoid sending to model)
- **File downloads** — capture downloads with `expect_download()`
- **File uploads** — use Playwright's file chooser APIs
- **Page content** — `nova.page.content()` for raw HTML
- **Screenshots** — `nova.page.screenshot(path="screenshot.png")`
- **Precise selectors** — when you know the exact element

## Sensitive Input

Never pass sensitive data in prompts. Use Nova Act to focus the field, then Playwright to type:

```python
from getpass import getpass

nova.act("enter username janedoe and click on the password field")
nova.page.keyboard.type(getpass())  # typed directly, not sent to model
nova.act("sign in")
```

> **Caution:** If Nova Act takes a screenshot of a page displaying sensitive information (including data entered via Playwright), that information will be captured in the screenshot.

## File Download

```python
with nova.page.expect_download() as download_info:
    nova.act("click on the download button")

download_info.value.save_as("my_downloaded_file")
```

For non-HTML content (e.g., PDF) on the current page:

```python
response = nova.page.request.get(nova.page.url)
with open("downloaded.pdf", "wb") as f:
    f.write(response.body())
```

## Page Content

```python
# Get rendered DOM as HTML
html = nova.page.content()

# Get current URL
url = nova.page.url
```

## Constraints

- `nova.page` is only available with Playwright-based actuators (not when using CDP-only via `cdp_endpoint_url`)
- Must call after `nova.start()` or inside `with NovaAct(...) as nova:` block
- Playwright actions happen outside the model's awareness — the model won't know what you typed or clicked
