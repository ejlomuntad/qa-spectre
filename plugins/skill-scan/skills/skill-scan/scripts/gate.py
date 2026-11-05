#!/usr/bin/env python3
"""skill-scan merge gate. No LLM: it only combines results and applies accepted.yml.

Inputs:
  --patterns     JSON lines from scan-patterns.pl (deterministic layer)
  --result       result.json from the Claude layer (optional)
  --deep-status  ran | local | skipped-fork | skipped-no-key | failed | no-targets
                 (local = the repo runs the deep scan on the maintainer's machine, not in CI)
  --patterns-ok  "true" only if the pattern job succeeded (otherwise the gate never passes)
  --accepted     accepted.yml converted to JSON (a list), optional
  --targets      file with the scanned folders, one per line
  --comment      where to write the PR comment (Markdown)

Exit code 0 = merge allowed, 1 = blocked (⚠️ or ❌).
The verdict and score are recomputed here from the findings. Claude's own verdict
is never trusted, so scanned content can't talk its way to a ✅.
"""
import argparse
import json
import os
import re
import sys

MARKER = "<!-- skill-scan-gate -->"
WEIGHTS = {"critical": 40, "high": 20, "medium": 8, "low": 3}
FP_PREFIX = "false-positive:"
SECRET_RE = re.compile(r"(?<![A-Za-z0-9])(sk-ant-|sk_live_|sk_test_|sk-|ghp_|gho_|ghs_|ghu_|ghr_|github_pat_|glpat-|xox[baprs]-|npm_|AIza|AKIA)([A-Za-z0-9_\\-]{4})[A-Za-z0-9_\\-]+")
JWT_RE = re.compile(r"\\beyJ[A-Za-z0-9_\\-]{8,}\\.[A-Za-z0-9_\\-]{8,}\\.[A-Za-z0-9_\\-]+")


def redact(text):
    """Never post a full secret, even if a finding quotes one."""
    text = SECRET_RE.sub(lambda m: m.group(1) + m.group(2) + "****", text)
    return JWT_RE.sub("eyJ****.****.****", text)


def unit_of(path, targets):
    """The skill a file belongs to: its nearest folder with a SKILL.md, else the scanned target."""
    d = os.path.dirname(path)
    while d:
        if os.path.isfile(os.path.join(d, "SKILL.md")) or os.path.isfile(os.path.join(d, "skill.md")):
            return d
        d = os.path.dirname(d)
    best = [t for t in targets if path == t or path.startswith(t.rstrip("/") + "/")]
    return max(best, key=len) if best else (os.path.dirname(path) or path)


def load_jsonl(path):
    out = []
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
    except FileNotFoundError:
        pass
    return out


def load_json(path, default):
    if not path:
        return default
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def code(text, limit=150):
    """Untrusted text as a code span in a table cell. Code spans render no HTML or @mentions."""
    text = redact(" ".join(str(text or "").split()))
    if len(text) > limit:
        text = text[:limit] + "…"
    return "`" + (text.replace("`", "'").replace("|", "\\|") or " ") + "`"


def where(file, line):
    return code(f"{file}:{line}", 120)


def cell(text, limit=150):
    """Make untrusted text safe for a Markdown table cell in a PR comment."""
    text = redact(" ".join(str(text or "").split()))
    if len(text) > limit:
        text = text[:limit] + "…"
    return (text.replace("\\", "\\\\").replace("|", "\\|").replace("<", "&lt;")
            .replace(">", "&gt;").replace("@", "&#64;").replace("`", "'")
            .replace("](", "] (").replace("![", "! ["))  # no links or images


class Accepted:
    def __init__(self, entries):
        self.entries = []
        self.invalid = []
        for e in entries if isinstance(entries, list) else []:
            if not isinstance(e, dict) or not e.get("id") or not e.get("file") or not str(e.get("reason", "")).strip():
                self.invalid.append((e, "needs id, file and reason"))
                continue
            if not e.get("match") and not e.get("match_regex"):
                self.invalid.append((e, "needs match or match_regex"))
                continue
            if e.get("match_regex"):
                try:
                    re.compile(e["match_regex"])
                except re.error as err:
                    self.invalid.append((e, f"bad match_regex: {err}"))
                    continue
            e["_used"] = False
            self.entries.append(e)

    def find(self, rule, file, text, strict, layer):
        """strict = block pattern or Critical finding: reason must start with 'false-positive:'.
        A wildcard id "*" only covers pattern matches, never Claude findings."""
        for e in self.entries:
            if not (e["id"] == rule or (e["id"] == "*" and layer == "patterns")):
                continue
            f = e["file"]
            if not (file == f or (f.endswith("/") and file.startswith(f))):
                continue
            text = text or ""
            if e.get("match") and e["match"] not in text:
                continue
            if e.get("match_regex") and not re.search(e["match_regex"], text):
                continue
            if strict and not str(e["reason"]).strip().lower().startswith(FP_PREFIX):
                continue
            e["_used"] = True
            return e
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patterns", required=True)
    ap.add_argument("--result")
    ap.add_argument("--deep-status", required=True)
    ap.add_argument("--patterns-ok", default="false")
    ap.add_argument("--accepted")
    ap.add_argument("--targets")
    ap.add_argument("--comment", required=True)
    ap.add_argument("--run-url", default="")
    a = ap.parse_args()

    targets = []
    if a.targets:
        try:
            targets = [t.strip() for t in open(a.targets, encoding="utf-8") if t.strip()]
        except FileNotFoundError:
            pass
    hits = load_jsonl(a.patterns)
    acc = Accepted(load_json(a.accepted, []))

    # Deterministic layer
    block_open, block_acc, cand_open = [], [], []
    for h in hits:
        if h.get("ci") == "block":
            e = acc.find(h["id"], h["file"], h.get("text"), strict=True, layer="patterns")
            (block_acc if e else block_open).append((h, e))
        else:
            if not acc.find(h["id"], h["file"], h.get("text"), strict=False, layer="patterns"):
                cand_open.append(h)

    # Claude layer
    deep = a.deep_status
    result = load_json(a.result, None) if deep == "ran" else None
    if deep == "ran" and (not isinstance(result, dict) or not isinstance(result.get("findings"), list)):
        deep = "failed"
    find_open, find_acc = [], []
    for f in (result or {}).get("findings", []):
        sev = str(f.get("severity", "")).lower()
        if sev not in WEIGHTS:
            continue  # info
        e = acc.find(str(f.get("rule", "")), str(f.get("file", "")), f.get("quote"), strict=(sev == "critical"), layer="deep")
        (find_acc if e else find_open).append((f, e))

    # Score each skill on its own (the 0-100 scale is per skill), then take the lowest.
    counts = {s: 0 for s in WEIGHTS}
    per_unit = {}
    for f, _ in find_open:
        sev = f["severity"].lower()
        counts[sev] += 1
        u = unit_of(str(f.get("file", "")), targets)
        per_unit[u] = per_unit.get(u, 100) - WEIGHTS[sev]
    unit_scores = {u: max(0, v) for u, v in per_unit.items()}
    score = min(unit_scores.values()) if unit_scores else 100

    reasons = []
    patterns_ok = a.patterns_ok == "true"
    if not patterns_ok:
        verdict = "review"
        reasons.append("The pattern check job failed, so nothing can be confirmed. See the workflow run.")
    elif not targets:
        verdict = "ok"
        reasons.append("No skills, plugins or MCP configs changed in this PR.")
    else:
        if block_open:
            reasons.append(f"{len(block_open)} high-confidence pattern match(es) (CI `block`).")
        if counts["critical"]:
            reasons.append(f"{counts['critical']} Critical finding(s).")
        if counts["high"]:
            reasons.append(f"{counts['high']} High finding(s).")
        if deep == "ran" and score < 70:
            low = [u for u, v in unit_scores.items() if v < 70]
            reasons.append("Risk score under 70 for: " + ", ".join(f"{code(u, 100)} ({unit_scores[u]})" for u in sorted(low)) + ".")
        if deep == "skipped-fork":
            reasons.append("Deep scan didn't run: PRs from forks get no secrets. The maintainer runs `/skill-scan:skill-scan changed` locally before merging.")
        elif deep == "skipped-no-key":
            reasons.append("Deep scan didn't run: the `ANTHROPIC_API_KEY` secret isn't set.")
        elif deep == "failed":
            reasons.append("Deep scan failed or returned no valid result.json. See the workflow run.")
        if block_open or counts["critical"]:
            verdict = "blocked"
        elif reasons:
            verdict = "review"
        elif deep == "local":
            verdict = "ok"
            reasons.append("The free pattern check found nothing that blocks the merge.")
            reasons.append("**Deep scan runs locally:** before merging, run `/skill-scan:skill-scan changed` in Claude Code on your machine (your own Claude login, no key on GitHub).")
        else:
            verdict = "ok"
            reasons.append("Only Medium or Low findings: the merge is allowed. Fix them when you can."
                           if find_open else "No open findings.")

    label = {"ok": "✅ OK to merge", "review": "⚠️ Fix or accept before merging", "blocked": "❌ Blocked"}[verdict]
    if verdict == "ok" and deep == "local" and targets:
        # Don't let a pattern-only pass read as "fully scanned".
        label = "✅ Pattern check passed: run the deep scan locally before merging"
    L = [MARKER, f"## skill-scan: {label}", ""]
    if targets:
        score_txt = (f"Lowest skill risk score **{score}/100**" if deep == "ran"
                     else "Pattern check only (deep scan runs locally)" if deep == "local"
                     else "Risk score: n/a (deep scan didn't run)")
        L.append(f"{score_txt} · Scanned: " + ", ".join(f"{code(t, 80)}" for t in targets))
        L.append("")
    L += [f"- {r}" for r in reasons] + [""]
    if len(unit_scores) > 1:
        L += ["| Skill | Score |", "|---|---|"]
        L += [f"| {code(u, 100)} | {v} |" for u, v in sorted(unit_scores.items(), key=lambda x: x[1])] + [""]

    if block_open:
        L += ["### Pattern matches that block the merge", "", "| Rule | Where | Line |", "|---|---|---|"]
        L += [f"| {cell(h['id'])} | {where(h['file'], h['line'])} | {code(h.get('text'))} |" for h, _ in block_open]
        L.append("")
    if find_open:
        L += ["### Findings", "", "| # | Severity | Rule | Where | What | Fix |", "|---|---|---|---|---|---|"]
        order = list(WEIGHTS)
        for i, (f, _) in enumerate(sorted(find_open, key=lambda x: order.index(x[0]["severity"].lower())), 1):
            L.append(f"| {i} | {cell(f['severity']).capitalize()} | {cell(f.get('rule'))} | "
                     f"{where(f.get('file'), f.get('line', ''))} | {code(f.get('quote'))} — {cell(f.get('why'))} | {cell(f.get('fix'))} |")
        L.append("")
    if cand_open and deep != "ran" and targets:
        L += ["<details><summary>Pattern candidates for manual review (" + str(len(cand_open)) + ")</summary>", "",
              "| Rule | Where | Line |", "|---|---|---|"]
        L += [f"| {cell(h['id'])} | {where(h['file'], h['line'])} | {code(h.get('text'))} |" for h in cand_open[:100]]
        L += ["", "</details>", ""]
    accepted_rows = [(h["id"], h["file"], e) for h, e in block_acc] + [(f.get("rule"), f.get("file"), e) for f, e in find_acc]
    if accepted_rows:
        L += ["<details><summary>Accepted (" + str(len(accepted_rows)) + ")</summary>", "", "| Rule | File | Reason |", "|---|---|---|"]
        L += [f"| {cell(r)} | {code(fl, 100)} | {cell(e['reason'])} |" for r, fl, e in accepted_rows]
        L += ["", "</details>", ""]
    if acc.invalid:
        L += ["### Invalid entries in `.github/skill-scan/accepted.yml`", ""]
        L += [f"- {code(json.dumps(e), 120)}: {cell(why)}" for e, why in acc.invalid] + [""]

    if verdict != "ok":
        L += ["### How to clear this", "",
              "1. **Fix it:** run `/skill-scan:skill-scan <skill folder>` locally for the full report, change the lines above, and push. The scan re-runs and this comment updates.",
              "2. **Or accept it** (false alarm or intended behaviour): add an entry to `.github/skill-scan/accepted.yml` with `id`, `file`, `match` and a `reason`. "
              "`block` matches and Critical findings need a reason starting with `false-positive:`.",
              ""]
    if a.run_url:
        L.append(f"Full report: workflow artifacts on [this run]({a.run_url}).")

    with open(a.comment, "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")
    print(f"verdict={verdict} score={score} block_open={len(block_open)} findings_open={len(find_open)} deep={deep}")
    sys.exit(0 if verdict == "ok" else 1)


if __name__ == "__main__":
    main()
