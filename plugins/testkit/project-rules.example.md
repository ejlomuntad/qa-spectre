# Testkit project rules

The testkit skills work out of the box on any software project. This file is where you add what's specific to yours: where things live, your domain terms and business rules, the words you must or must not use, and how your tickets look.

**This file is a template.** The skills never read it from here. Project rules are optional: without them, the skills use generic defaults.

**How to use it:** copy this file and fill in only the sections you need. Delete or leave empty anything that doesn't apply. The skills use the first of these that exists:

1. A file you point to with `rules=<path or GitHub link>`, e.g. `rules=docs/qa/project-rules.md` or a shared team repo
2. `<your project>/.claude/testkit/project-rules.md` (per repo; commit it to share with your team)
3. `~/.claude/testkit/project-rules.md` (on your machine, for all your projects)

Keep secrets out of this file. It's plain text, and the skills quote from it.

---

## Repos and folders

Where the skills should look for requirements, code and tests.

- Requirements and specs (PRD, user stories, acceptance criteria, design docs): `docs/requirements/`
- API spec: `openapi.yaml`
- Source code for the service under test: `src/`
- API tests (e.g. Postman collection and environment): `tests/postman/`
- Local start command and port (only if you test against local servers): `npm run dev` (port 3000)
- API test tool: `<e.g. Postman, Bruno, Insomnia, REST Assured, Karate, pytest, Jest, Playwright, k6>`
- API test command (how your team runs the API tests): `npm run test:api`
- API test results (the report your command writes, JUnit XML or newman JSON): `reports/api-junit.xml`
- Test hosts (safe to run tests against; api-audit asks about any other host): `localhost`, `api-test.example.com`
- Main output folder (replaces `~/Desktop/Testkit`, keeps the same subfolders): `~/Documents/Testkit/`
- When documents disagree, which wins: `<e.g. requirements, then API spec, then business rules>`

## Domain glossary and business rules

Terms and rules a tester needs that aren't in the requirements, or that the requirements assume. The skills use these to read the docs correctly and to build edge cases.

| Term or rule | Meaning |
|---|---|
| `<e.g. Order>` | `<e.g. a confirmed cart; can't be edited after payment>` |
| `<e.g. Refund window>` | `<e.g. 30 days from delivery, not from purchase>` |

## Units and formats

Values that are easy to get wrong between documents and code.

- Money: `<e.g. stored in cents, shown in dollars with 2 decimals>`
- Dates and time zones: `<e.g. UTC in the API, local time in the UI>`
- IDs: `<e.g. UUID v4>`

## Test case tags

Tags `create-testcase` adds to each test case, for filtering after import.

- `<e.g. web, mobile, api>`
- `<e.g. smoke, regression>`

## Terminology and compliance

Words your content must or must not use, for example in test case titles, tickets or user-facing copy. `create-testcase` flags these in source documents.

| Don't use | Use instead | Why |
|---|---|---|
| `<word>` | `<word>` | `<rule>` |

## Issue tracker

How tickets and pass notes should look.

- Tracker: `<Jira, GitHub Issues, Linear, ...>`
- Project key or repo: `<e.g. SHOP>`
- Ticket ID format: `<e.g. SHOP-1234>`
- Required fields: `<e.g. Environment, Build, Steps, Expected, Actual>`
