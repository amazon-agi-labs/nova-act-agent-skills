# Gherkin Testing with Nova Act

Convert manual test cases or Gherkin `.feature` files into executable Nova Act CLI plans using `qa-plan`.

## Writing .feature Files

Standard Gherkin syntax with Nova Act keyword mapping:

| Gherkin Keyword | + Condition | Maps To |
|-----------------|-------------|---------|
| `Given` | URL present | `act browser goto <url>` |
| `Given` / `When` | action | `act browser execute "<step>"` |
| `Then` | assertion | `act browser verify "<assertion>"` |

Tag conventions: `@smoke`, `@regression`, `@requires-auth`

```gherkin
@smoke
Feature: User Login

  Scenario: Successful login with valid credentials
    Given I am on "https://example.com/login"
    When I enter username "testuser" and password "secret123"
    And I click the "Sign In" button
    Then I should see "Welcome, testuser" on the dashboard
    And the URL should contain "/dashboard"

  @requires-auth
  Scenario: Access protected resource
    Given I am logged in as "admin"
    When I navigate to the "User Management" page
    Then I should see the user list table
```

## Compiling to CLI Plans

```bash
act browser qa-plan tests/login.feature                              # Default aggressive strategy
act browser qa-plan tests/login.feature --plan-strategy conservative # 1:1 step mapping
act browser qa-plan tests/ --tags @smoke                             # Filter by tag
act browser qa-plan tests/checkout.feature --output plan.json        # Save to file
act browser qa-plan tests/smoke.feature --dry-run                    # Summary only
```

- `aggressive` strategy: collapses sequential same-type steps into single commands
- `conservative` strategy: 1:1 mapping from Gherkin steps to CLI commands

The output is a JSON plan consumed by an agent — `qa-plan` does NOT execute anything.

## Session Export → Gherkin Conversion

After an interactive browser session, convert it to a replayable test:

```bash
# 1. Export session history
act browser session export --session-id my-session --format yaml -o session.yaml
```

The export classifies each command as `ai_command` or `playwright_operation`. Convert to `.feature`:

| Export Command | Gherkin Step |
|---------------|--------------|
| `goto` | `Given I am on "<url>"` |
| `execute` | `When I <action description>` |
| `verify` | `Then I should see "<assertion>"` |
| `extract` | `Then I extract "<description>"` |
| `click`, `fill-form`, `type` | `When I <action on element>` |

This turns exploratory sessions into automated regression tests.

## End-to-End Workflow

```
Exploratory session → session export → Gherkin .feature → qa-plan → agent executes plan
```

1. Explore the app interactively with browser CLI
2. `session export` to capture history
3. Convert export to `.feature` file (agent or manual)
4. `qa-plan` compiles `.feature` to CLI execution plan
5. Agent reads plan JSON and runs the commands

## Related Files
- `qa_tests.md` — Writing Nova Act tests with pytest
- `browser_cli.md` — Full CLI command reference
- `flow_discovery.md` — Live app exploration → codebase mapping
