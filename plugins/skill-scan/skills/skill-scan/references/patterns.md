# Pattern checks

> This file lists attack patterns so the scanner can find them. **It is reference data, not instructions.** When `skill-scan` scans itself, matches in this file are expected and aren't findings.

Run each pattern against the target as `command grep -rnEi '<pattern>' <target> --exclude-dir=node_modules --exclude-dir=.git`. Use `command grep`, not plain `grep`: in Claude Code's shell `grep` can be a wrapper (e.g. `ugrep`) that rejects some of these patterns. The table cells escape `|` as `\|`; drop the backslash when you run them. A literal pipe character is written `[|]`. Use `-i` unless a row says "case-sensitive". Every match is a candidate. Confirm it in Step 4.

`scripts/scan-patterns.pl` runs every row of this file, so local scans and CI give the same matches. Edit the tables here, not the script. The **CI** column says how the pre-merge gate treats an unaccepted match:
- `block`: high-confidence on its own. Fails the gate even if the Claude layer didn't run.
- `candidate`: needs judgement. Claude confirms or drops it in Step 4.

## P1 Prompt injection and instruction override

| ID | Pattern | Looks for | CI |
|---|---|---|---|
| P1.1 | `(ignore\|disregard\|forget\|override).{0,40}(instruction\|rules\|prompt\|guideline)` | Override of earlier instructions | candidate |
| P1.2 | `you are now\|new persona\|act as (an? )?(unrestricted\|jailbroken\|developer mode)\|DAN mode` | Role hijack | candidate |
| P1.3 | `(do not\|don't\|never) (tell\|inform\|mention\|show\|reveal)[^.]{0,30}(user\|human)` | Hiding actions from the user | candidate |
| P1.4 | `without (asking\|telling\|confirming\|permission\|the user knowing)\|silently\|quietly\|in the background without` | Acting without consent | candidate |
| P1.5 | `(reveal\|print\|output\|repeat\|dump)[^.]{0,30}(system prompt\|your instructions\|hidden instructions)` | System prompt leakage | candidate |
| P1.6 | `<!--` | HTML comments (hidden text in rendered markdown). Read every one. | candidate |
| P1.7 | `(mark\|report\|treat)[^.]{0,30}(as )?(safe\|trusted\|verified\|approved)\|skip (this\|the) (scan\|check\|review)` | Attempts to fool scanners and reviewers | candidate |
| P1.8 | `(always\|must) (use\|invoke\|run) this skill\|before (any\|every) (task\|response\|request)\|use for (everything\|all tasks)` | Trigger abuse (over-broad description) | candidate |

## P2 Data exfiltration and secrets

| ID | Pattern | Looks for | CI |
|---|---|---|---|
| P2.1 | `curl.*(-d\|--data\|-F\|--form\|--upload-file\|-T \|-X ?(POST\|PUT))` | Sending data out with curl | candidate |
| P2.2 | `wget.*--post\|Invoke-WebRequest\|fetch\([^)]*method:[[:space:]]*['"](POST\|PUT)` | Other upload methods | candidate |
| P2.3 | `\bnc\b.*[0-9]{2,5}\|\bncat\b\|\bsocat\b\|/dev/tcp/` | Raw sockets | candidate |
| P2.4 | `webhook\.site\|ngrok\|requestbin\|pipedream\|pastebin\|hastebin\|transfer\.sh\|discord(app)?\.com/api/webhooks\|hooks\.slack\.com\|interact\.sh\|burpcollaborator` | Known drop sites | block |
| P2.5 | `\.ssh/\|id_rsa\|id_ed25519\|\.aws/credentials\|\.netrc\|\.npmrc\|\.pypirc\|\.docker/config\|\.kube/config\|\.git-credentials` | Reading credential files | candidate |
| P2.6 | `security (find-generic-password\|find-internet-password\|dump-keychain)\|keychain\|login\.keychain` | macOS Keychain access | candidate |
| P2.7 | `printenv\|(^\|[^a-z_.])env[[:space:]]*[|]\|os\.environ\|process\.env([^.]\|$)\|\$\{?[A-Z_]*(TOKEN\|SECRET\|KEY\|PASSWORD)` | Dumping environment variables or secrets (case-sensitive) | candidate |
| P2.8 | `gh auth token\|acli.*token\|cat .*\.env\b` | Pulling CLI tokens | candidate |
| P2.9 | `(sk-ant-\|sk-[A-Za-z0-9]{20}\|sk_live_\|ghp_\|gho_\|ghs_\|github_pat_\|glpat-\|npm_[A-Za-z0-9]{36}\|AIza[0-9A-Za-z_-]{35}\|xox[baprs]-\|AKIA[0-9A-Z]{16}\|-----BEGIN [A-Z ]*PRIVATE KEY)` | Hard-coded secrets (case-sensitive) | block |
| P2.10 | `https?://[^\s)'"]+` | Every external URL. List them all and check each host in Step 4. | candidate |

## P3 Dangerous execution

| ID | Pattern | Looks for | CI |
|---|---|---|---|
| P3.1 | `(curl\|wget).*[|][[:space:]]*(sudo[[:space:]]+)?(ba\|z)?sh([^a-z]\|$)\|(curl\|wget).*[|][[:space:]]*(python\|node\|perl)` | Download and execute | block |
| P3.2 | `\beval\b\|\bexec[[:space:]]*\(\|new Function\(\|child_process\|subprocess\|os\.system\|spawn\(\|execSync` | Dynamic code execution | candidate |
| P3.3 | `base64 (-d\|--decode)\|atob\(\|b64decode\|fromCharCode\|xxd -r` | Decoding hidden payloads | candidate |
| P3.4 | `rm -rf\|rm -fr\|git (reset --hard\|clean -fd\|push (-f\|--force))\|--no-verify\|mkfs\|dd if=` | Destructive commands | candidate |
| P3.5 | `\bsudo\b\|chmod (777\|\+s\|u\+s)\|chown root` | Privilege escalation | candidate |
| P3.6 | `dangerouslyDisableSandbox\|dangerously-skip-permissions\|--yolo\|bypassPermissions\|"defaultMode":[[:space:]]*"(bypass\|auto)` | Turning off safety controls | block |

## P4 Persistence and configuration tampering

| ID | Pattern | Looks for | CI |
|---|---|---|---|
| P4.1 | `\.zshrc\|\.bashrc\|\.bash_profile\|\.profile\|crontab\|LaunchAgents\|LaunchDaemons\|launchctl\|systemd` | Startup and persistence hooks | candidate |
| P4.2 | `settings(\.local)?\.json\|"hooks"\|PreToolUse\|PostToolUse\|SessionStart\|UserPromptSubmit` | Claude Code settings and hooks | candidate |
| P4.3 | `"permissions"\|"allow"[[:space:]]*:\|allowedTools\|--allowedTools` | Granting itself permissions | candidate |
| P4.4 | `CLAUDE\.md\|AGENTS\.md\|MEMORY\.md\|/memory/\|\.claude/(skills\|agents\|commands)` | Writing to instructions, memory or other skills (memory poisoning, self-spreading) | candidate |
| P4.5 | `\.git/hooks\|core\.hooksPath\|husky` | Git hooks | candidate |

## P5 Supply chain

| ID | Pattern | Looks for | CI |
|---|---|---|---|
| P5.1 | `npm (i\|install)\|npx \|pnpm (add\|dlx)\|yarn (add\|dlx)\|pip3? install\|uvx? \|pipx\|brew install\|cargo install\|go install\|gem install` | Installs things | candidate |
| P5.2 | `@latest\|curl.*raw\.githubusercontent\|git clone` | Unpinned or remote code | candidate |
| P5.3 | `postinstall\|preinstall\|"prepare"[[:space:]]*:` | Install-time scripts in any `package.json` | candidate |

## P6 Excessive agency and outward actions

| ID | Pattern | Looks for | CI |
|---|---|---|---|
| P6.1 | `^allowed-tools:.*` | Tools the skill asks for. Compare them with what it actually needs (Step 4). | candidate |
| P6.2 | `gh (pr (create\|merge\|comment\|review\|close)\|issue (create\|comment\|close)\|api .*-X ?(POST\|PATCH\|PUT\|DELETE)\|release create\|repo (delete\|edit))` | GitHub write actions | candidate |
| P6.3 | `acli.*(create\|edit\|transition\|comment\|delete\|update)` | Jira and Confluence write actions | candidate |
| P6.4 | `slack\|chat\.postMessage\|sendmail\|smtp\|mail -s` | Messaging and email | candidate |
| P6.5 | `git (commit\|push)` | Commits and pushes | candidate |

## P7 Obfuscation and hidden content

| ID | Command | Looks for | CI |
|---|---|---|---|
| P7.1 | `command grep -rnE '[A-Za-z0-9+/]{120,}={0,2}' <target>` | Long base64 blobs | candidate |
| P7.2 | `command grep -rnE '(\\x[0-9a-fA-F]{2}){8,}\|(\\u[0-9a-fA-F]{4}){6,}' <target>` | Escaped byte strings | candidate |
| P7.3 | `find <target> -type f -exec perl -CSD -ne 'print "$ARGV:$.: zero-width/bidi\n" if /\x{200B}\|\x{200C}\|\x{200D}\|\x{2060}\|\x{FEFF}\|[\x{202A}-\x{202E}]\|[\x{2066}-\x{2069}]/; close ARGV if eof' {} +` | Invisible and right-to-left characters | block |
| P7.4 | `find <target> -type f -exec perl -CSD -ne 'print "$ARGV:$.: tag chars\n" if /[\x{E0000}-\x{E007F}]/; close ARGV if eof' {} +` | Unicode tag characters (invisible prompt text) | block |
| P7.5 | `find <target> -type f -exec awk 'length > 2000 {print FILENAME":"FNR": "length" chars"}' {} +` | Very long lines (minified or packed code) | candidate |
| P7.6 | `find <target> -type f \( -name '*.zip' -o -name '*.tar*' -o -name '*.gz' -o -name '*.exe' -o -name '*.dylib' -o -name '*.so' -o -name '*.bin' -o -name '*.pyc' -o -name '*.wasm' \)` | Binaries, archives, files the scanner can't read, symlinks and vendored `node_modules` | block |

## P8 MCP servers

Run on every `.mcp.json`, `plugin.json` and `settings*.json`:

| ID | Pattern | Looks for | CI |
|---|---|---|---|
| P8.1 | `"command"[[:space:]]*:\|"args"[[:space:]]*:\|"url"[[:space:]]*:` | What each MCP server launches or connects to | candidate |
| P8.2 | `"env"[[:space:]]*:` | Secrets passed to a server | candidate |
| P8.3 | `awk '/"description"[[:space:]]*:/ && length > 300 {print FILENAME":"FNR}' <file>` | Very long tool descriptions (where tool poisoning hides) | candidate |
