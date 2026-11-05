# Ticket mode (API bug ticket)

Re-verifies one bug, saves JSON evidence and writes a copy-paste bug ticket for the engineers. Follow the project rules' issue-tracker format (tracker, project key, ID format, required fields) if given; otherwise use the format below. When the source of truth isn't explicit, reason from what it does say (related rules, the API spec, how the same case behaves in another endpoint or feature) and write the expected section as "please confirm".

## Step 1: Locate inputs

| Input | Usual location |
|---|---|
| Source of truth | the shared requirements inventory (SKILL.md, Requirements) and the API spec; cite the rule by inventory ID and document section |
| Source code | the project rules' source folder, otherwise `src/` or similar (only to understand the bug; never quoted in the ticket) |
| API tests | the project rules' API tests folder, otherwise search (see `references/audit.md`, Step 1) |
| Latest main | the separate checkout of upstream main, `<work>/main/` (SKILL.md, Paths), updated and built |

Test **upstream main**, not a stale branch, so the bug isn't already fixed. Check the ledger first: if this bug already has a ticket line, update it rather than writing a duplicate.

## Step 2: Double-check that it really is a bug

Don't write a ticket until all three agree:
1. **Source of truth:** the exact document and section, or the rule text. If documents disagree (e.g. requirements vs API spec), say which one you followed and why.
2. **Code:** it does what the API shows (for your understanding only).
3. **API:** reproduced with real requests on the project's test servers (restarted first if they're local; SKILL.md, Test servers and test runs).

- Use test data that gives a clean, known state; start chains with setup requests that create or reset the data.
- Add a **control case** when it helps (the same request with one input changed, or a valid request next to the invalid one).
- Check the same case on related endpoints or roles. An inconsistency between them is strong evidence.
- If the evidence says it's NOT a bug, stop and tell the user why. Don't write the ticket.

## Step 3: Save the evidence

Write a small script under `<work>` that runs the repro against the same servers as the collection, after the host check (SKILL.md, Test servers and test runs). It saves every request/response to the bug evidence folder in the **evidence format** below. Leave out tokens and secrets.

**Evidence format** (ticket and pass-note evidence use the same one, so before and after files compare directly): one file per step, `NN-<label>.json`, numbered `01`, `02` …, with
```json
{ "step": "refund-more-than-paid", "endpoint": "POST /orders/{id}/refunds", "request": { "body": {} }, "response": { "status": 201, "body": {} } }
```
Labels describe the step (e.g. `03-refund-more-than-paid-accepted.json`).

## Step 4: Write the ticket

Start with: `Written for: the <project> engineering team, as a bug ticket you copy and paste into <tracker>.`

- **Title:** one line describing the wrong behaviour.
- **Type:** Bug
- **Component:** `<project> API (<feature>)`
- **Priority:** High if it corrupts data, affects money, breaks security or blocks a main flow; Medium for wrong behaviour with small impact; Low for cosmetic response fields.
- **Description:** what happens in plain words, and where (endpoint, role, state).
- **Steps to reproduce** (environment, user/role, server, and the API test tool used, e.g. "Bruno 1.20"): numbered. Give the method, endpoint and key body fields, and the key response fields after each important step.
- **Expected (source of truth):** quote the document and section or rule (and its inventory ID, e.g. `R-04`), then a table of expected values. Add "please confirm" (and "if this is intended, please point us to the rule") when the source of truth isn't explicit.
- **Actual (API):** a table of actual values per case, wrong values in bold. Include the stored data or balance change when data or money is affected.
- **Impact:** who is affected, how often, the effect on data, money or security, which endpoints.
- **Evidence:** the folder path, a `Files | Content` table, and "Attach at least …" with the key files.

Add any required fields from the project rules.

## Step 5: Ledger

If the ledger exists, add or update the ticket line (`references/ledger.md`): `ID pending`, status `open — not filed yet`. When the user says it's filed, set `open` and fill in the ticket ID. If there's no ledger, skip this; don't create one.

## Step 6: Intentional-failure test (only with the go-ahead)

- Offer a test (in the project's API test tool) that asserts the **correct** (source of truth) value, so it fails until the fix lands. Say where it goes (folder, request names, expected values) and wait.
- Back up first, follow the rules in `references/audit.md`, Follow-up work (the project's own framework and style), then rerun the **whole** test suite (restarting local servers first) and list the intentional failures.
- Add the test to the ledger's Intentional failures with the same ticket ID/title.
