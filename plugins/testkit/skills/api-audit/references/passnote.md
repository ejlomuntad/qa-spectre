# Passnote mode (fix verification)

After the engineer's fix PR is merged, re-verify the ticket(s) through the API and write a copy-paste PASS or FAIL comment for your issue tracker with fresh evidence. Use the project rules' issue-tracker format if given.

## Step 0: Get the PR (required)

If the request has no PR number or URL, **ask and stop until the user answers**:

> Please provide the engineer's PR for this fix (number or URL), and the ticket ID(s) if the PR covers more than one bug.

## Step 1: Read the PR

```bash
gh pr view <PR> --json number,title,body,state,mergedAt,baseRefName,headRefName,commits,files
```

- Confirm it's **merged** into main. If not, tell the user and ask whether to test the PR branch instead.
- Map each ticket ID to its bug from the PR title, body and commits. If a mapping is a guess, say so.
- Find the original repro and expected values: the ledger's ticket line, its bug evidence folder, memory, or ask the user.

## Step 2: Build the fixed version

- Update the separate checkout of upstream main, `<work>/main/` (SKILL.md, Paths), to a commit that includes the PR, then build.
- Read the version from that commit (e.g. `package.json`, the spec's `info.version`), or use the short commit hash.
- Check the hosts and, for local servers, restart them (SKILL.md, Test servers and test runs).

## Step 3: Re-verify through the API

- Re-run the original repro (and any control case) on every endpoint, role and state the ticket mentions.
- Run the **whole** API test suite the way the project does, and read the report with `read_results.py` (SKILL.md, Test servers and test runs).
  - The bug's intentional failures should now pass.
  - If tests asserted the old (buggy) behaviour, propose the updates and wait for the go-ahead. Then back up, update, format and rerun.
- Count the relevant checks for the notes (e.g. "all 48 refund checks pass").
- If the fix doesn't work, or works only partly, **don't write PASS.** Write the same comment with `API test result: FAIL` and expected vs actual values, and offer to update the bug ticket.
- Note any new side effect of the fix (e.g. a new error code or a changed response field) and ask whether it's accepted before calling it PASS.

## Step 4: Save fresh evidence

Save the requests and responses from the fixed build to the fix evidence folder, one folder per ticket, in the same **evidence format** as the bug ticket (`references/ticket.md`, Step 3): `NN-<label>.json` with `step`, `endpoint`, `request` and `response`. Use the same step numbers as the bug evidence where you re-run the same step, so before and after line up. Leave out tokens and secrets. Labels show what the file proves (e.g. `03-refund-more-than-paid-rejected-422.json`).

## Step 5: Write the comment(s)

Start with: `Written for: the ticket(s) <IDs>, as copy-paste PASS comments.` When the PR covers several tickets, write one comment each under `### <TICKET-ID>: <bug title>`.

```
**Build:**
<project> <version> (main; includes PR #<n>)

**API test result:** PASS

**Pass Notes:**
- What the API does now, compared with before ("now X. It used to Y.").
- Where it was checked (each endpoint, role and state involved).
- A table of the key steps: the response fields that prove the fix (status code, error code, the changed fields, stored data …), fixed value in bold.
- Why the values are right, using the source of truth (document + section or rule).
- Full API test suite (<tool and its version, e.g. "Postman / newman 6.2.3">, suite version <version>, <N> tests): all <n> <relevant> checks pass.

**(Attached evidence)**
Folder `<folder-name>`:
- `01-<file>.json`
- ...
```

Then tell the user briefly:
- which mappings were guesses
- where the evidence folders are
- anything left over (old evidence folders, tests still to update, side effects to accept)

## Step 6: Ledger

If the ledger exists, update each ticket's line (`references/ledger.md`):
- **PASS:** `fixed — PR #<n>, version <version>, verified <date> | fix evidence <folder>`. Remove its Intentional failures. If old-behaviour tests were updated, say so in one line.
- **FAIL:** `still open — retest FAILED <date> (PR #<n>, version <version>)` plus what's still wrong. Keep its intentional failures.
- **Accepted side effect:** add it to Decisions with the date.
- Ticket not in the ledger yet: add its line with the new status.

If there's no ledger, skip this; don't create one.
