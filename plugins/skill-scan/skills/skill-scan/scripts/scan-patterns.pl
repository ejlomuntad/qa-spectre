# skill-scan

Read-only security scan of AI agent skills, plugins and MCP configs before you install or share them. It reads a skill folder, a `SKILL.md`, a plugin, a `.mcp.json` or a GitHub repo, runs pattern checks plus a full read-through (prompt injection, data exfiltration, dangerous commands, persistence, supply chain, excessive agency, obfuscation), and gives a 0–100 risk score, a verdict and a Markdown report. It never runs, installs or edits the scanned code.

## Install

This skill is the `skill-scan` plugin. See [Install](../../../../README.md#3-install) in the main README.

## Use

```
/skill-scan:skill-scan <path | SKILL.md | plugin folder | .mcp.json | GitHub URL | skill name | all | repo | changed>
```

- `repo`: every skill and plugin in the current repo.
- `changed`: only what changed since `origin/main` (or `changed=<branch>`). Use it before you push.

Reports are saved to `~/Desktop/skill-scan-output/` (on Windows, the Desktop you actually see, e.g. the OneDrive Desktop). The skill tells you the full path.

The pattern pass is a script, so you can also run it on its own (no Claude needed):

```
perl scripts/scan-patterns.pl <folder>
```

## Trust list (optional)

By default only a small baseline counts as normal: `localhost` calls, read-only `gh` calls to the scanned repo, docs links and files inside the skill. Any other host needs a reason that fits the skill's job.

To mark your own orgs, hosts and CLIs as expected, copy `trusted.example.md` to `./.claude/skill-scan/trusted.md` (per project) or `~/.claude/skill-scan/trusted.md` (global) and edit it. The project file is used first.

## Pre-merge check on pull requests

skill-scan can also run on every PR in your own skills repo and block the merge until problems are fixed. It uses the reusable workflow [`.github/workflows/skill-scan.yml`](../../../../.github/workflows/skill-scan.yml) in this repo.

**Set it up** with `/skill-scan:skill-scan setup-ci` in your repo, or copy [`templates/caller-workflow.yml`](templates/caller-workflow.yml) to `.github/workflows/skill-scan.yml` yourself and replace both `<commit-sha>` placeholders with a commit SHA of this repo. Then make `skill-scan / gate` a required check: **Settings → Branches → Add rule** for `main` → "Require status checks to pass" (and "Require review from Code Owners").

**No secret needed.** By default (`deep_scan: local`) GitHub runs only the free pattern check and the gate. The deep scan, where Claude reads every file, runs **on your machine** with your normal Claude Code login: before merging a PR, run `/skill-scan:skill-scan changed`.

| Job | What it does | Needs |
|---|---|---|
| `patterns` | Runs `scan-patterns.pl` on the changed skills, plugins, `.claude/` files, `CLAUDE.md` and `AGENTS.md` | Nothing |
| `deep-scan` | Only with `deep_scan: ci`: Claude follows this skill in `ci` mode and writes `result.json`. It gets no shell beyond `ls`, runs no repo scripts, and doesn't load the scanned repo's settings, hooks or MCP servers | `deep_scan: ci` and an `ANTHROPIC_API_KEY` secret (billed to that key). Skipped for PRs from forks |
| `gate` | No AI. Combines the results, applies your accepted-findings file, posts one PR comment, passes or fails | Nothing |

The scanner, this skill and the gate always come from this repo (`scanner_ref`), not from the PR, so a PR can't weaken its own check without editing the workflow file.

**The merge is blocked** by any unaccepted CI `block` pattern match (see the CI column in `references/patterns.md`). With `deep_scan: ci`, also by any Critical or High finding, a skill scoring under 70, or a deep scan that didn't run.

**When the check fails:**
1. Read the PR comment. Each finding has its file, line and a suggested fix. With `deep_scan: ci`, the full report is in the run's `skill-scan-deep` artifact; with `local`, the pattern matches are in the `skill-scan-patterns` artifact.
2. Run `/skill-scan:skill-scan <skill folder>` locally for the same report.
3. Either **fix** the lines and push (the scan re-runs and the comment updates), or **accept** a false alarm: add an entry with a reason to `.github/skill-scan/accepted.yml` (format: [`templates/accepted.example.yml`](templates/accepted.example.yml)). `block` matches and Critical findings need a reason starting with `false-positive:`.
4. Merge when the `gate` check is green.

**Limits:** a PR can still edit the workflow file itself. Review every change under `.github/` before merging.
