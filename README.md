# Nova Act Agent Skills

Agent skills and a [Kiro power](https://kiro.dev/docs/powers/) for [Amazon Nova Act](https://github.com/aws/nova-act) — an AI-powered browser automation SDK for web scraping, testing, and workflow automation.

## What's Included

This repository contains skills and powers that extend AI coding assistants with Nova Act capabilities:

| Format | Directory | Entry Point | For |
|--------|-----------|-------------|-----|
| Agent Skill — Nova Act | `skills/nova-act/` | `SKILL.md` | Browser automation, data extraction, QA testing, workflow automation |
| Agent Skill — UI Verification | `skills/ui-verification/` | `SKILL.md` | Visual and flow verification of live web apps against design specs |
| Kiro Power — Nova Act | `powers/nova-act/` | `POWER.md` | [Kiro](https://kiro.dev) IDE power for Nova Act |

All skills follow the [Agent Skills](https://agentskills.io) specification and are compatible with [Kiro IDE](https://kiro.dev/docs/), [Kiro CLI](https://kiro.dev/docs/cli/), Claude Code, Codex, and other [supported clients](https://agentskills.io/clients).

## Skills

Install both skills with the [skills CLI](https://github.com/vercel-labs/skills):

```bash
npx skills@latest add amazon-agi-labs/nova-act-agent-skills
```

Or copy the skill directories manually:

```bash
# Kiro (global)
cp -r skills/nova-act/ ~/.kiro/skills/nova-act/
cp -r skills/ui-verification/ ~/.kiro/skills/ui-verification/

# Kiro (project-level)
cp -r skills/nova-act/ .kiro/skills/nova-act/
cp -r skills/ui-verification/ .kiro/skills/ui-verification/

# Claude Code
cp -r skills/nova-act/ .claude/skills/nova-act/
cp -r skills/ui-verification/ .claude/skills/ui-verification/
```

### Nova Act

Browser automation skill for web scraping, testing, and workflow automation. Covers authentication, session management, data extraction, parallel sessions, Playwright interop, and more.

See [docs/nova-act.md](docs/nova-act.md) for full usage details.

### UI Verification

Verifies whether a live web app matches its design specification. Two modes:

- **Visual verification** — deterministic CSS checks against the live DOM (colors, typography, spacing, components, accessibility)
- **Flow verification** — executes flow scenarios end-to-end via Nova Act

Generates a combined report with annotated screenshots and per-flow detail. Requires the [amazon-nova-act-mcp](https://github.com/amazon-agi-labs/amazon-nova-act-mcp) server with the `ui-verification` toolset enabled.

See [docs/ui-verification.md](docs/ui-verification.md) for full usage details.

## Using the Kiro Power

1. Open [Kiro](https://kiro.dev)
2. Click the lightning bolt icon in the sidebar
3. Select **Add Custom Power**
4. Point to the `powers/nova-act/` directory in this repository
5. The power will appear in your powers list

See [docs/kiro-power.md](docs/kiro-power.md) for full usage details.

## Repository Structure

```
├── skills/
│   ├── nova-act/              # Agent Skill — browser automation
│   │   ├── SKILL.md           # Main skill definition
│   │   └── references/        # Detailed reference documents
│   └── ui-verification/       # Agent Skill — visual + flow verification
│       ├── SKILL.md           # Main skill definition
│       └── references/        # Detailed reference documents
├── powers/
│   └── nova-act/              # Kiro Power
│       ├── POWER.md           # Main power definition
│       └── steering/          # Steering documents
├── docs/                      # Usage guides
│   ├── nova-act.md            # Nova Act skill guide
│   ├── ui-verification.md     # UI Verification skill guide
│   └── kiro-power.md          # Kiro Power guide
├── LICENSE                    # Apache-2.0
├── CONTRIBUTING.md
└── README.md
```

## Learn More

- [Nova Act SDK](https://github.com/aws/nova-act) — the SDK itself
- [Nova Act Documentation](https://docs.aws.amazon.com/nova-act/latest/userguide/what-is-nova-act.html) — official AWS docs
- [Agent Skills Specification](https://agentskills.io/specification) — the skill format standard
- [Kiro](https://kiro.dev) — the IDE that supports powers

## Security

See [CONTRIBUTING.md](CONTRIBUTING.md) for reporting security issues.

## License

This project is licensed under the Apache-2.0 License. See [LICENSE](LICENSE) for details.
