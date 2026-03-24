# Nova Act Agent Skill

An [agent skill](https://agentskills.io) and [Kiro power](https://kiro.dev/docs/powers/) for [Amazon Nova Act](https://github.com/aws/nova-act) — an AI-powered browser automation SDK for web scraping, testing, and workflow automation.

## What's Included

This repository contains two formats of the same Nova Act guidance:

| Format | Directory | Entry Point | For |
|--------|-----------|-------------|-----|
| Agent Skill | `skills/nova-act/` | `SKILL.md` | AI coding assistants that support the [Agent Skills](https://agentskills.io) specification |
| Kiro Power | `powers/nova-act/` | `POWER.md` | [Kiro](https://kiro.dev) IDE |

Both contain the same core content — onboarding guides, authentication patterns, data extraction techniques, QA testing patterns, observability tools, and more.

## Using the Kiro Power

1. Open [Kiro](https://kiro.dev)
2. Click the lightning bolt icon in the sidebar
3. Select **Add Custom Power**
4. Point to the `powers/nova-act/` directory in this repository
5. The power will appear in your powers list

## Repository Structure

```
├── skills/
│   └── nova-act/              # Agent Skill (agentskills.io format)
│       ├── SKILL.md           # Main skill definition
│       └── references/        # Detailed reference documents
├── powers/
│   └── nova-act/              # Kiro Power
│       ├── POWER.md           # Main power definition
│       └── steering/          # Steering documents
├── LICENSE                    # Apache-2.0
├── CONTRIBUTING.md
└── README.md
```

## Linting

Run all lint checks and schema validation:

```bash
make check
```

Run just the lint checks (frontmatter, references, tokens, cross-references, parity):

```bash
make lint
```

Individual check groups are available via `make lint-frontmatter`, `make lint-references`, `make lint-tokens`, `make lint-crossrefs`, and `make lint-parity`.

## Branch Protection

To make the lint check required before merging PRs:

1. Go to the repo **Settings → Branches**
2. Click **Add branch protection rule** (or edit the existing `main` rule)
3. Set **Branch name pattern** to `main`
4. Enable **Require status checks to pass before merging**
5. Search for and select the **Lint** status check
6. Save changes

After this, PRs targeting `main` cannot be merged until `make check` passes.

## Learn More

- [Nova Act SDK](https://github.com/aws/nova-act) — the SDK itself
- [Nova Act Documentation](https://docs.aws.amazon.com/nova/latest/userguide/using-nova-act.html) — official AWS docs
- [Agent Skills Specification](https://agentskills.io/specification) — the skill format standard
- [Kiro](https://kiro.dev) — the IDE that supports powers

## Security

See [CONTRIBUTING.md](CONTRIBUTING.md) for reporting security issues.

## License

This project is licensed under the Apache-2.0 License. See [LICENSE](LICENSE) for details.
