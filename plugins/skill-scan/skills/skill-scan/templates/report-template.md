# Skill scan report template

Use this layout for both the chat reply and the saved file. Leave out empty sections. For `all`, repeat the "Skill" block per skill and start with the summary table.

---

# Skill scan: <skill name>

**Date:** YYYY-MM-DD · **Target:** `<path or repo URL>` · **Files scanned:** <n> · **Trust list:** `<path>` or none

## Verdict: <✅ OK to install | ⚠️ Review before installing | ❌ Do not install> · Risk score <0–100>/100

(CI mode: ✅ OK to merge | ⚠️ Fix or accept before merging | ❌ Blocked.)

<One or two plain sentences: what the skill does and the main reason for the verdict.>

| Critical | High | Medium | Low | Info |
|---|---|---|---|---|
| n | n | n | n | n |

## Findings

| # | Severity | Category | Where | What it does | Why it matters | Fix |
|---|---|---|---|---|---|---|
| 1 | Critical | Data exfiltration | `scripts/sync.sh:12` | `<short quote>` | <plain-language risk> | <concrete change> |

Category is one of: Prompt injection, Data exfiltration, Secrets, Dangerous execution, Persistence, Supply chain, Excessive agency, Obfuscation, MCP, Trigger abuse, Purpose mismatch.

## Capabilities

| Capability | Used? | Where |
|---|---|---|
| Tools requested (`allowed-tools`) | <list> | `SKILL.md:<line>` |
| Runs shell commands | yes / no | |
| Contacts external hosts | <hosts> | |
| Outward actions (Jira, GitHub, Slack, email) | <which; confirm step yes/no> | |
| Writes files | <where> | |
| Installs or downloads code | yes / no | |
| Hooks or auto-run | yes / no | |

## Left out on purpose
- <candidate>: <why it isn't a finding, e.g. "curl to localhost for a local dev API">

## Not checked
- <item>: <why, e.g. "binary file, can't be read">

---

### Summary table (only for `all`)

| Skill | Verdict | Score | C | H | M | L |
|---|---|---|---|---|---|---|
