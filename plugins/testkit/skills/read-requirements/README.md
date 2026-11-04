# read-requirements

Read a project's documents once and get a clear, cited summary of what they require, plus the contradictions and open questions to send to your product owner. No tests are written.

## Install

This skill is part of the `testkit` plugin. See [Install](../../../../README.md#3-install) in the main README.

## When to use it

- **Before testing starts:** find gaps and contradictions in the PRD and send the questions to the product owner first.
- **To make documents readable:** get readable copies of Excel, Word and PowerPoint files, with their pictures.
- **To prepare for the other skills:** `api-test-plan` and `create-testcase` reuse what this skill saves, so they don't read the documents again.

You don't have to run it first. `api-test-plan` and `create-testcase` do the same reading themselves if there's nothing saved yet.

## Usage

```
/testkit:read-requirements [<docs path | GitHub link>] [spec=<openapi/schema paths or links>] [rules=<path or link>]
```

1. It asks for the **project name** (e.g. `orders-service`).
2. It looks for the documents the same way as every testkit skill: the path or link you give, otherwise the files this project used last time, otherwise `~/Desktop/Testkit/qa-docs/<project>/`, otherwise the project rules requirements folder. When it found them itself, it lists them and asks "Use these?".
3. It converts Office files, reads everything, and saves the result.

File types: see [Which files can I use?](../../../../README.md#which-files-can-i-use).

## What you get

Saved in `~/Desktop/Testkit/requirements/<project>/`:

```
~/Desktop/Testkit/requirements/<project>/
├── requirements-inventory.md   what the documents require, every item cited
├── sources.json                which files were read, and a fingerprint of each
└── converted/                  readable copies of Office files, and their pictures
```

The inventory has numbered, cited items in these sections: features and flows (`F-01`), business rules (`R-01`), API endpoints, fields and errors (`E-01`, `ERR-01`), UI and screens (`U-01`), states (`S-01`), limits (`L-01`), behaviour (`B-01`), integrations (`I-01`), **contradictions** (`C-01`), **open questions** (`Q-01`) and what wasn't covered.

In the chat it shows the counts, and **every contradiction and open question in full**, ready to send to the product owner.

## Reuse

The next time any testkit skill reads documents for the same project, it checks the fingerprints:
- **nothing changed** → it offers to reuse the saved inventory;
- **a file changed or was added** → it tells you which, and offers to read them again;
- **different documents** → it asks whether to add them to the project, replace it, or save them under a new name.

It never reuses without asking.
