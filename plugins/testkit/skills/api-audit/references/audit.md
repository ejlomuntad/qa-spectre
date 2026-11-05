# Audit mode (per feature, incremental)

For agile teams that deliver a service one feature at a time. A feature is whatever the team ships as one piece: an endpoint group, a user story or an epic. The audit:
- covers **only the feature(s) the team has finished**.
- **never reports a feature that isn't built yet as a bug or a gap.** List it once as "not in scope yet".
- re-checks the features audited before (regression), using the ledger.

It's a three-way comparison of **source of truth vs implementation vs tests**. For the feature in scope, find:
1. **Implementation bugs**: the code or API differs from the source of truth.
2. **Test bugs**: tests that pass only because they assert the buggy value, check the response against itself, or send data the source of truth doesn't allow.
3. **Coverage gaps**: rules or test-plan scenarios for this feature that no request exercises, with coverage as a %.
4. **Test plan gaps**: rules, edge cases and interactions the test plan itself doesn't list. Report them; never edit the test plan.

Steps 0–6 are read-only: don't modify any repo file. Write work files only under `<work>` (SKILL.md, Paths), and the ledger only in `<evidence>/feature-audit/<project>/`.

## Step 0: Load the ledger

If there is no ledger, this is the first increment; create it in Step 7. If there is one, note:
- the features already audited (date, spec version, code commit, assertion count)
- the user's decisions. **Never re-raise these.**
- tickets filed and intentional failures
- open items carried forward

## Step 1: Choose the feature and locate inputs

**Feature.** Use the one in the request. Otherwise build the feature list from the requirements (epics, user stories), the API spec (tags, paths) and the source code (routes, handlers, modules). Typical features: create / read / update / delete for each resource · auth and permissions · validation · search and pagination · state changes (e.g. order placed → paid → shipped) · integrations and webhooks · limits and rate limits.

Ask (AskUserQuestion, multiSelect) which features the team has finished, and mark the ones already in the ledger.

- **If a feature depends on one that isn't built yet,** only check the part that exists (e.g. the request is accepted and stored). Mark the rest as "pending <feature>".

**Inputs.** Use the project rules' folders if given; otherwise search. Show them in a table and get a quick confirmation.

| Input | Common locations (examples) |
|---|---|
| Requirements and business rules | **The shared requirements inventory** (SKILL.md, Requirements): `<root>/requirements/<project>/requirements-inventory.md`. Reused if the documents are unchanged; otherwise the workflow finds and reads them (the user's path or link, last time's files, `<root>/qa-docs/<project>/`, the project rules folder) and converts Office files. Plus the project rules' glossary and business rules |
| API spec | `openapi.yaml`, `openapi.json`, `swagger.*`, `api/*.yaml`, GraphQL schema |
| Test plan (optional) | `<root>/api-test-plan/<project>/<project>-api-test-plan.md` (the `api-test-plan` skill's output for the same project), otherwise `docs/test-plan*.md` or `tests/test-plan/` |
| Source code | `src/`, `app/`, `server/`: routes, handlers, validators, models, database schema |
| API test suite (+ tool) | The project rules' API tests folder first. Name the tool and version (SKILL.md, **Which tool**). Otherwise: a Postman collection + environment (`*.postman_collection.json`, `*environment.json`), or another tool's API tests, e.g. Bruno (`*.bru`), Insomnia (`.insomnia/`), REST Assured or Karate (`src/test/…`), pytest, Jest/Supertest, Playwright or k6 (`tests/api/`, `test/`, `e2e/`) |
| Version | the spec's `info.version`, `package.json` version, or the requirements doc version |

- No API spec: fine. Use the requirements and the project rules only, and say so.
- No API tests yet: fine for an early increment. Coverage is "Missing" for everything in scope; offer to write the feature's tests after the report.
- **Changes since the last increment** (skip on the first run): `git log --oneline <ledger commit>..HEAD -- <source dir> <spec file>` for the code and spec; for the requirements, the workflow's fingerprint check says which documents changed. Changes touching audited features are the regression targets for Step 5.

## Step 2: Baseline run

Check the hosts and, for local servers, restart them (SKILL.md, Test servers and test runs). Then run the **whole** API test suite the way the project does (same section: the project rules' API test command, the project's own test command, or newman for a Postman collection), with a JUnit XML or newman JSON report. Read the report with `read_results.py` into `<work>/run1-results.json` (SKILL.md, Test servers and test runs). The newman default looks like this:

```bash
cd '<collection dir>'
npx -y newman@6.2.3 run '<collection>.json' -e '<environment>.json' \
  --reporters json --reporter-json-export '<work>/run1.json' > /dev/null 2>&1
```

Save a reusable `<work>/run.sh <report>` that runs the suite and reads the report. Summarise each run from the results file: tests, passed, failed, errors and skipped, and failures grouped by suite and test.

Report separately:
- requests that never sent
- real failures
- the ledger's intentional failures, and whether each still fails

Compare the assertion count with the ledger. **0 failures doesn't mean "correct"**: the tests may assert the buggy behaviour.


## Step 3: Test index

Write `<work>/test-index.md`, one line per test, tagged with its feature:
- **Postman:** from the collection JSON: folder path, request name, method + endpoint, auth used, key body fields, `pm.test` titles.
- **Other tools:** from the test files: file and test name, the method + endpoint it calls, key inputs, and what it asserts (status, fields, values).

The results file from Step 2 gives each test's outcome; for newman it also has the real request and response, so read the actual response values there.

## Step 4: Two parallel read-only agents (scoped to the feature)

Launch both in one message, in the background, with the `testkit:doc-reader` agent type (read-only: Read, Glob and Grep only). They read requirements, specs and code you don't control. They return text; you run any scripts (e.g. `execmap.mjs`) yourself and pass them the output. Give each:
- the feature and its boundaries
- the feature's part of the requirements inventory (its F-, R-, E-, ERR-, S-, L-, B- and I- items, plus related contradictions and open questions)
- the project rules' glossary, business rules and units, if any
- the ledger decisions, which must not be re-raised
- **read-only: no files, no commands**

**Agent A: source of truth vs tests (coverage and test plan gaps).**

First build the feature's **rule list** independently of the test plan: start from the inventory items for the feature (each keeps its ID, e.g. `R-04`), then add the edge cases they imply:
- required and optional fields, missing fields, wrong types, empty values, extra fields
- min / max lengths and values, limits, boundaries (just inside, on, just outside)
- units and formats from the project rules (money, dates and time zones, IDs)
- auth: no token, expired token, wrong role, another user's resource
- state transitions: each allowed one, and the ones that must be rejected (e.g. refund before payment)
- duplicates and idempotency, concurrent updates, not found, pagination ends
- interactions with features already audited

Then map both lists to the API tests:
- **Covered**: exercised AND asserted
- **Partial**: exercised but not asserted, or only the happy path / one role
- **Missing**

Map by behaviour, not field name; read the real assertion code for anything non-obvious. Coverage % = (Covered + ½ Partial) / total, computed separately for each list.

Then compare the two lists: every rule or edge case with no matching test-plan scenario is a **test plan gap**. If there is no test plan, say so and measure coverage against the rule list only.

Output:
1. counts and coverage % against the test plan and against the rule list
2. a Partial/Missing table with a concrete suggested request (method, endpoint, key body fields, expected status) per row
3. a test plan gaps table: `# | rule / edge case (document + section) | suggested scenario | also missing in the tests?`
4. a compact covered list
5. suspected test bugs
6. field-name mismatches and stale values between the plan, the spec and the code

**Agent B: source of truth vs implementation.** Go rule by rule through the feature's inventory items and the spec, and find what the code does for each. If a rule's exact wording matters, open the cited document section. Where a scripted comparison would help (e.g. routes, schemas, enums), describe it in the return value: you (the orchestrator) write and run it, then check the result. Checklist:
- **Endpoints:** every spec path and method exists; no undocumented ones in scope
- **Requests:** required fields, types, formats, enums, defaults, min/max, unknown fields
- **Responses:** status codes per case, body shape, field names and types, nullability, headers
- **Errors:** error format and codes match the spec; the right status for validation, auth, not found and conflict
- **Validation and business rules:** every rule in the requirements and project rules is enforced, at the right point, with the right message or code
- **State transitions:** allowed and rejected transitions, side effects (stored data, events, emails, webhooks)
- **Auth and permissions:** who can call it, who can see which fields, ownership checks
- **Limits:** page sizes, rate limits, size limits, timeouts
- **Units and formats:** money, dates, time zones, rounding, IDs (project rules)
- **Idempotency and concurrency:** retries, duplicate requests, parallel updates

Look hard at **boundaries with features already audited**: the same resource changed by two features, state left behind by one feature and read by the next. Skip interactions with unbuilt features and list them as "pending".

Output:
- a table: `# | area | source of truth (inventory ID + document + section) | implementation (file:line) | tests assert | severity (data / behavioural / cosmetic) | caught by tests? (no / yes / asserts the buggy value — name the request)`
- the list of things verified as matching
- ambiguities in the source of truth, with the code's current choice

## Step 5: Verify and regression-check

**Verify each suspected bug yourself.** Don't pass agent findings on unchecked:
- confirm it in the code AND the source of truth
- reproduce it through the local API and record the actual values
- mark it **confirmed** (source of truth + code + API) or **unverified** (agent only)

Merge both agents' output into one three-way view per rule: what the source of truth says, what the API does, and what the tests assert. Spec and code agree but tests differ → test bug. Spec and tests agree but code differs → implementation bug (the tests should be failing; if they aren't, also a test bug). Code and tests agree but the spec differs → implementation bug that the tests hide. All three silent or unclear → clarification question.

**Regression of earlier features:**
- Audited features must still pass in the baseline run; a new failure there is a regression.
- For each repo change touching an audited feature, re-check that area.
- For each ticket and intentional failure: does the check pass now (fixed but not yet verified)? Does a `fixed` check fail again (regression → set it back to `open`)?

## Step 6: Report

Concise markdown, starting with:

> **Feature audited:** … · **Previously audited:** … · **Not in scope yet:** …
> **API tests:** <tool> <version> (<N> tests in the suite) · **Run against:** <hosts>

If no project rules were found, say so in one line.

1. **Likely implementation bugs (this feature):** source of truth vs API, severity, confirmed/unverified, and whether the tests catch it, miss it or **assert the buggy value** (name the requests). Data-impacting first (wrong stored data, money, security).
2. **Clarification questions:** gaps or ambiguities in the source of truth, with what the code does now.
3. **Coverage:** Covered/Partial/Missing counts and % against the test plan and against the rule list (e.g. "plan 38/42 = 90% · rules 51/60 = 85%"), then the most useful gaps with a suggested request each.
4. **Test plan gaps:** rules, edge cases and interactions the plan doesn't list, each with a suggested scenario, and whether the tests miss it too. Also list stale plan values (e.g. limits that don't match the spec). These are for the plan owner; the audit doesn't edit the plan.
5. **Test bugs:** e.g. expected values copied from the response; assertions that only check the status code; requests that send data the spec forbids and still expect success; wrong limits; wrong titles.
6. **Regression check:** earlier features OK / regressed (with evidence). Ticket statuses, including checks that now pass unverified (suggest `passnote`) and `fixed` ones failing again.
7. **Pending:** interactions and rules waiting on unbuilt features (the targets for the next increment).
8. **Housekeeping**, if any (e.g. spec version vs test suite version mismatch). Mention it once.

End with a recommended order, data and security bugs first.

**Then ask about each confirmed implementation bug, one at a time** (AskUserQuestion):

> Bug #1 (refunds): a refund larger than the payment returns 201, the requirements say it must be rejected with 422. Is this a bug, and should I create the ticket?
> - Yes, it's a bug: create the ticket
> - No, it's intended / follow the code
> - Not sure yet: ask the engineers or product first

- **Yes:** continue in ticket mode (`references/ticket.md`) with `<feature>: <short bug description>`.
- **No:** add it to the ledger's Decisions.
- **Not sure:** add it to the ledger's Pending list as a clarification question.

Never ticket unverified items or clarification questions. Then stop; the user picks what's next, one item at a time.

## Step 7: Update the ledger

After the report, and again after any follow-up work, create or update the ledger (`references/ledger.md`): add the Increments row, Decisions, Pending, Intentional failures and regression status changes.

---

## Follow-up work (only when the user asks)

**Story tickets** (e.g. coverage that needs unit tests): start with "Written for: …", no code, and evidence in the story evidence folder.

**Changing or adding tests:**
- First say where the change goes (folder, request names, expected values) and wait for the go-ahead. Back up what you'll change (the collection, or the test files) to `<evidence>/backups/<project>/<YYYY-MM-DD>-<change>/` (SKILL.md, Paths).
- **Postman:** edit the collection as below. **Any other tool:** write the test in the project's own framework and style, next to similar tests (copy the structure of an existing test file). Never add a new framework, library or dependency.
- Use one folder (or test file) per feature (e.g. `01 Create order`, `02 Payment`, `03 Refunds`); each increment adds its own and leaves earlier ones alone.
- Prefer re-runnable generator scripts. Use test data no other folder uses (its own user, its own IDs), so state can't leak between folders. Start chains with a setup request that creates or resets the data.
- Work out expected values independently (from the source of truth, by hand or your own script), never by copying the response. Then confirm them through the API.
- For a known bug, assert the **correct** (source of truth / user-agreed) value, so the test fails until the fix lands. Record it as an intentional failure in the ledger.
- **Formatting** (Postman; follow the project's own style for other tools): assertion literals with 2+ elements go one element per line; short rows stay inline.
  ```js
  pm.expect(body.items).to.eql([
      { sku: "A-1", qty: 2 },
      { sku: "B-7", qty: 1 }
  ])
  ```
  Request bodies are multi-line JSON with short arrays inline (`"tags": ["gift","express"]`).
- After every change, rerun the **whole** test suite (restarting local servers first). Only the known intentional failures should remain, and the assertion count shouldn't drop unexpectedly.
