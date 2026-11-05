# The ledger

There's one ledger per project (or service): `<evidence>/feature-audit/<project>/ledger.md`. It's the only state the modes share, and the hand-over between increments.

| Mode | Reads | Writes |
|---|---|---|
| audit | everything | Increments, Decisions, Pending, Intentional failures. **Creates the ledger** on the first run |
| ticket | existing ticket lines (avoid duplicates) | the ticket line; the bug's intentional failures |
| passnote | the ticket line, its evidence folder | the ticket status; removes intentional failures on PASS; accepted side effects under Decisions |

Only audit creates a ledger. Ticket and passnote update it if it exists, and skip it otherwise.

## Template

```markdown
# <project> — feature audit ledger

## Increments
| Date | Feature | Spec version | Code commit | Test tool | Test assertions | Coverage (plan · rules) | Test plan gaps | Result |
|---|---|---|---|---|---|---|---|---|

If the tool changes between increments (e.g. Postman → Bruno), say so in the report: assertion counts and coverage aren't directly comparable across tools.

## Decisions (do not re-raise)
- <date> <feature>: <decision> (user)

## Tickets filed
- <TICKET-ID or "ID pending"> | <feature> | <title> | filed <date> | evidence <folder> | status: <status>

## Intentional failures in the test suite
- <request name> — asserts <correct value>, API returns <value> — ticket <ID/title>

## Pending (waiting on unbuilt features, or clarification questions)
- <feature>: <rule / interaction / question>
```

## Ticket statuses

| Status | Set by | When |
|---|---|---|
| `open — not filed yet` | ticket | ticket written, not in the tracker yet (ID `ID pending`) |
| `open` | ticket / status | the user says it's filed; fill in the ticket ID |
| `fixed — PR #<n>, version <version>, verified <date> \| fix evidence <folder>` | passnote | retest PASSED |
| `still open — retest FAILED <date> (PR #<n>, version <version>)` + what's still wrong | passnote | the fix didn't work |
| back to `open` | audit | a `fixed` check fails again (regression) |

## Rules

- Update the existing line. Never add a duplicate; match by ticket ID, or by title/evidence folder while the ID is pending.
- Use absolute dates (YYYY-MM-DD).
- Keep it factual and short.
