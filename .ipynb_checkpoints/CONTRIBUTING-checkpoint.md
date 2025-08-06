# Contributing to OriginFlow

Thank you for your interest in contributing to OriginFlow! We welcome contributions from the community to help improve the platform. This document outlines the process for contributing code, documentation, or other improvements.

## Code of Conduct
By participating in this project, you agree to abide by our Code of Conduct (CODE_OF_CONDUCT.md). Please report unacceptable behavior to maintainers@originflow.dev.

## How to Contribute
1. **Fork the Repository**: Click the "Fork" button on GitHub to create your own copy.
2. **Create a Branch**: Use descriptive names, e.g., `feat/new-agent` for features, `fix/bug-123` for bugs, `docs/update-readme` for docs.
3. **Make Changes**: Follow guidelines in AGENTS.md for code, especially for AI agents (use Spec Cards from ENGINEERING_PLAYBOOK.md).
4. **Commit Standards**: Use conventional commits (e.g., `feat: add new agent`), keep messages clear (<50 chars for title).
5. **Test Locally**: Run `./scripts/lint.sh && ./scripts/test.sh`. For agents, add unit/e2e tests (>90% coverage).
6. **Push and PR**: Push to your fork and open a PR against main. Use the PR template below.

## Pull Request Template
Use this in your PR description:

**Description**
Brief overview of changes (e.g., "Adds LeadDiscoveryAgent with web_search tool").

**Related Issues**
Closes #123

**Changes**
- Added backend/agents/lead_discovery_agent.py
- Updated AGENT_TAXONOMY.md

**Testing**
- Unit: pytest backend/agents/test_lead_discovery.py
- Manual: Ran agent execute with sample input

**Checklist**
- Tests pass
- Docs updated (e.g., README.md, AGENTS.md)
- Spec Card added for new agents
- Bias/ethics audit if bias_guard: true
- No breaking changes (or deprecated)

## For AI Agents
- Follow ENGINEERING_PLAYBOOK.md: Start with Spec Card, implement AgentInterface.
- Add to registry.py and taxonomy in AGENT_TAXONOMY.md.
- Test for hallucinations/bias (e.g., LangChain evaluators, AIF360).
- Use events for dependencies (no direct calls).

## Review Process
- PRs reviewed within 48h.
- Require 1+ approval; squash merges.
- CI must pass (lint, tests, coverage).

## Questions?
Join #originflow-dev on Slack or email maintainers@originflow.dev.
