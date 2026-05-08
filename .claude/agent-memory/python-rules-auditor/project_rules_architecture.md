---
name: Rules architecture
description: How project coding rules are split across CLAUDE.md and .claude/rules/, with progressive-disclosure routing
type: project
---

The project uses progressive disclosure: `CLAUDE.md` at the project root is the index, and `.claude/rules/` contains topic files (`python-rules.md`, `naming-rules.md`, `scalability-rules.md`). `.claude/skills/new-feature/SKILL.md` and `.claude/skills/pre-deploy/SKILL.md` carry rule-shaped guidance too (boilerplate templates and deployment gates), and `.claude/agents/fastapi-security-auditor.md` defines the security review checklist.

**Why:** Audits must cover all five files, not just CLAUDE.md — skills and agents embed implicit rules (e.g. the new-feature SKILL.md hard-codes `from typing import Dict` which contradicts python-rules.md).

**How to apply:** Whenever auditing, also diff skill/agent files against the canonical rule files for contradictions. Don't just audit CLAUDE.md and the rules/ folder.
