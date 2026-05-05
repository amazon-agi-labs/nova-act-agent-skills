# Nova Act Agent Skill

An [agent skill](https://agentskills.io) and [Kiro power](https://kiro.dev/docs/powers/) for [Amazon Nova Act](https://github.com/aws/nova-act) — an AI-powered browser automation SDK for web scraping, testing, and workflow automation.

## What's Included

This repository contains two formats of the same Nova Act guidance:

| Format | Directory | Entry Point | For |
|--------|-----------|-------------|-----|
| Agent Skill | `skills/nova-act/` | `SKILL.md` | AI coding assistants that support the [Agent Skills](https://agentskills.io) specification |
| Kiro Power | `powers/nova-act/` | `POWER.md` | [Kiro](https://kiro.dev) IDE |

Both contain the same core content — onboarding guides, authentication patterns, data extraction techniques, QA testing patterns, observability tools, and more.

## Using the Agent Skill

This skill follows the [Agent Skills](https://agentskills.io) format and is compatible with a [large number of AI tools and agentic clients](https://agentskills.io/clients), including [Kiro IDE](https://kiro.dev/docs/), [Kiro CLI](https://kiro.dev/docs/cli/), Claude Code, and Codex.

Install with the [skills CLI](https://github.com/vercel-labs/skills) for an interactive setup with your coding agents:

```bash
npx skills@latest add amazon-agi-labs/nova-act-agent-skills
```

Or copy/symlink `skills/nova-act/` into your agent's skills directory manually.

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

## Learn More

- [Nova Act SDK](https://github.com/aws/nova-act) — the SDK itself
- [Nova Act Documentation](https://docs.aws.amazon.com/nova-act/latest/userguide/what-is-nova-act.html) — official AWS docs
- [Agent Skills Specification](https://agentskills.io/specification) — the skill format standard
- [Kiro](https://kiro.dev) — the IDE that supports powers

## Security

See [CONTRIBUTING.md](CONTRIBUTING.md) for reporting security issues.

## License

This project is licensed under the Apache-2.0 License. See [LICENSE](LICENSE) for details.
