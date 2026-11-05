# Spectre SkillGuard — Agensi Edition

**Read-only security auditing for AI agent skills, plugins, and MCP configurations.**

Spectre SkillGuard helps you review an AI agent skill *before* you install or trust it. It checks for suspicious instructions, risky code, access to sensitive data, unexpected external connections, and other potentially unsafe behavior. It provides a structured report with evidence, severity ratings, a security score, and a recommended verdict.

> **Availability:** Spectre SkillGuard is offered as a standalone skill through [Agensi](https://www.agensi.io/). This page documents the Agensi edition; it is not an installation guide for the QA Spectre Claude Code plugin.

## What it does

- Reviews accessible skill folders, `SKILL.md` files, plugin folders, MCP configuration files, and Git repositories.
- Checks **46 security pattern rules** across eight categories, when automated scanning is supported.
- Performs contextual AI review to confirm or dismiss candidate findings rather than treating every matching string as a vulnerability.
- Reports file paths and line numbers for verified findings, with suggested remediation.
- Identifies unreadable, excluded, or unsupported files as **Not checked**.
- Produces a **0–100 risk score** and an installation recommendation.
- Operates **read-only against the target**: it does not install, execute, or modify code from the skill under review.

## Security categories

| Category | What it looks for |
| --- | --- |
| P1 — Prompt injection | Instructions attempting to override an agent's behavior or hide actions |
| P2 — Data exfiltration and secrets | Suspicious credential access, secret handling, or transfer of data |
| P3 — Dangerous execution | Risky shell commands, evaluation, injection paths, or destructive behavior |
| P4 — Persistence and configuration tampering | Unauthorized startup hooks, settings changes, or persistent modifications |
| P5 — Supply chain | Untrusted downloads, runtime dependencies, and installation risks |
| P6 — Excessive agency | Actions or permissions that go beyond the skill's stated purpose |
| P7 — Obfuscation and hidden content | Concealed instructions, unreadable material, or suspicious file handling |
| P8 — MCP servers | Unexpected MCP server configuration and capabilities |

The pattern checks are followed by contextual review. A pattern match is **not automatically a confirmed vulnerability**.

## Requirements

- A supported AI agent connected and signed in to **Agensi MCP**.
- Access to the skill folder, project files, or repository you want to inspect.
- **Perl 5** and permitted terminal execution for the automated pattern scanner.
- **Git** for Git repository operations and changed-file checks.

If terminal execution or Perl is unavailable, the agent may conduct a **limited manual review** using its available file-reading tools. The report should say when the automated scanner was not run. A remote repository can only be inspected when the agent has access to its contents and the necessary permissions.

## Getting started

1. Connect your AI agent to Agensi and sign in. See [Agensi's connection instructions](https://www.agensi.io/docs/mcp-server).
2. Purchase or access **Spectre SkillGuard** in Agensi.
3. In your AI agent, ask it to load the skill and specify the accessible target.
4. Review the report, especially any **Critical** or **High** findings and the **Not checked** section.
5. Address confirmed findings before deciding whether to install the scanned skill.

### Example requests

**Scan a local skill folder**

```text
Use my Agensi skill "Spectre SkillGuard" to audit
./tools/example-skill. Perform a read-only scan,
verify the findings, and show the security report.
```

**Scan the current repository**

```text
Use Spectre SkillGuard to review the skills and
plugin configurations in my current repository.
Report each affected file and any exclusions.
```

**Scan changes**

```text
Use Spectre SkillGuard to review skill-related
changes since origin/main in this repository.
If Git or the scanner is unavailable, tell me
what you could and could not inspect.
```

**Review a GitHub repository**

```text
Use Spectre SkillGuard to audit this GitHub repository:
<repository URL>
Read the relevant files without running their code.
```

Replace example paths with folders or repositories your connected agent can actually access. Commands and permissions vary by host.

## How the review works

1. **Inventory:** Identify entry points, scripts, agent instructions, configuration files, and excluded material.
2. **Pattern pass:** Run security checks when the scanner can be executed in the host environment.
3. **Contextual read-through:** Review the intended purpose and what the code or instructions actually do.
4. **Verification:** Confirm findings against accessible file contents and cite locations.
5. **Risk assessment:** Assign severities and calculate a score.
6. **Report:** Display a readable Markdown security report with next steps.

The skill is designed to inspect the target without running its code. Host-side operations such as reading files or obtaining a repository require the agent to have appropriate access.

## Understanding scores and verdicts

**Risk score:** Start at 100, then subtract **40** per Critical finding, **20** per High, **8** per Medium, and **3** per Low. The minimum score is zero. Informational items do not reduce the score.

| Verdict | Meaning |
| --- | --- |
| ✅ **OK to install** | No Critical or High findings, and the score is at least 70 |
| ⚠️ **Review before installing** | At least one High finding, or a score below 70 |
| ❌ **Do not install** | At least one Critical finding |

A favorable verdict is **not** a guarantee that the code is safe. The result depends on what was accessible and actually inspected.

## What the report includes

- The scan target, number of files reviewed, and any trust list used.
- Verdict and security score.
- Confirmed findings with severity, category, file location, explanation, and suggested fix.
- A summary of requested tools, commands, network contacts, and other capabilities.
- Suspicious matches dismissed after contextual review, when relevant.
- Files or content **not checked**, including binaries, inaccessible files, and unsupported material.

The agent displays the report in chat. Saving a Markdown copy is optional and depends on the host's capabilities and your authorization.

## Optional trust list

You can supply an optional list of expected GitHub organizations, hosts, repositories, and command-line tools. It helps the reviewer distinguish normal activity from unexpected access.

A trust list does **not** override Critical or High security findings. If no trust list is provided, the report should say so.

## Limitations and safety notes

- **No code execution from the scanned target.** The skill is for inspection, not sandboxing or malware detonation.
- **Not all files can be reviewed.** Binaries, archives, unreadable files, and symlink targets outside the scan scope may remain unchecked.
- **Automated detection is environment-dependent.** The Perl scanner requires Perl and authorized execution in the agent's host environment.
- **Manual review has limits.** Large or inaccessible projects may prevent a complete inspection.
- **Findings require verification.** Pattern matches can be false positives; subtle malicious behavior can be missed.
- **No automatic monitoring or CI gate** is included in this standalone Agensi edition.
- **No separate Claude Code helper agent** is required. The connected host AI agent performs contextual analysis.

## Agensi edition vs. Claude Code plugin

The **Agensi edition** is a standalone skill delivered through Agensi MCP. It does not install Claude Code plugin hooks, slash commands, or a separate helper agent.

The **QA Spectre GitHub project** may include a separate Claude Code-specific implementation. Its plugin setup and features are not requirements for using the Agensi edition.

## Frequently asked questions

**Does Spectre SkillGuard automatically prevent malicious skills from running?**  
No. It is an assessment tool. It produces findings and recommendations but does not install, block, or modify the scanned target.

**Do I need the `scan-reader` helper agent?**  
No. The Agensi edition uses the AI agent already connected to Agensi for contextual review.

**Can I use it without Perl?**  
A limited manual review may be possible if the host agent can read the target files. The report must disclose that the automated scanner did not run.

**Can it inspect private repositories?**  
Only when the host agent has legitimate access and any required permissions. Never paste passwords, personal access tokens, or private keys into a scan request.

**Can I use the score as proof that a skill is secure?**  
No. Treat the score as decision support, not a security certification.

---

**Project:** [QA Spectre on GitHub](https://github.com/ejlomuntad/qa-spectre)  
**Product:** Spectre SkillGuard — Agensi Edition  
**Documentation scope:** Public usage guide. The paid skill's implementation is distributed separately through Agensi.
