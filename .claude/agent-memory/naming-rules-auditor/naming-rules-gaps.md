---
name: naming-rules-gaps
description: Places where .claude/rules/naming-rules.md is silent or self-contradictory, surfaced during audits
type: project
---

Gaps in `naming-rules.md` v2.0.0 that forced judgement calls during the 2026-08-08 audit. Each was reported as a 🟢 Addition rather than a violation.

- **Framework-mandated method names have no exemption.** `_SecretScrubFilter.filter` (main.py:53) shadows the builtin `filter`, which rule Variables#7 bans — but `logging.Filter` requires that exact method name. Same class of problem: `BaseHTTPMiddleware.dispatch`, Pydantic's `model_config`.
- **Enum member casing is unspecified.** Classes#2 says enums end in `Status` but says nothing about members. `TaskStatus.ok/due_soon/overdue/never_done` are lowercase, which conflicts with Constants#1 if members count as constants.
- **`constants.py` has no specified location.** Constants#2 says "defined in constants.py only" without saying whether that means `backend/constants.py` or one per module.
- **`AnthropicConfig` is required by the contract table but does not exist.** The Claude model ID lives in `DashboardScanConfig.model` instead. The table promises a config class per service; nothing says what to do when a service's settings are a single field inside a feature config.
- **`get_config()` / `cfg` sit between two rules.** Functions#6 assigns `cfg_` to "config value handling", which would make it `cfg_get_app_config()`, but Functions#5 blesses bare verb+noun orchestrators. `cfg` as a parameter is fine since only `config` is banned.

**Why:** Without a ruling, each audit risks flagging these differently, which makes findings look inconsistent to the user.

**How to apply:** Do not report these as violations. Report as 🟢 Addition with the exact rule text to add, and record the user's ruling here as a [[type: feedback]] memory once they decide.

Related: [[backend-recurring-violations]]
