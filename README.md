# QA Spectre

Modular Claude Code skills and agent workflows for QA engineering, automated test design, and software quality assurance.

**New to Claude Code?** Start with [Getting started](#getting-started). It takes about 10 minutes.

## What's in here

### testkit

QA skills for any software project. They read your requirements, specs, code and API tests.

| Skill | What it does | You type |
|---|---|---|
| [read-requirements](plugins/testkit/skills/read-requirements) | Reads your documents once and saves a cited summary of the requirements, with contradictions and open questions for the product owner. Writes no tests | `/testkit:read-requirements` |
| [api-test-plan](plugins/testkit/skills/api-test-plan) | Builds an API test plan from requirements and specs, before or while the code is written | `/testkit:api-test-plan` |
| [create-testcase](plugins/testkit/skills/create-testcase) | Writes positive, negative and edge test cases from your documents, flags gaps and contradictions, and outputs MD and CSV for import | `/testkit:create-testcase` |
| [api-audit](plugins/testkit/skills/api-audit) | Audits each dev-complete feature against its requirements, the code and the API tests. Writes bug tickets, pass notes and a per-project status ledger | `/testkit:api-audit <project>` |

**How they work together.** The skills that need your requirements read them **once per project** and save the result in `~/Desktop/Testkit/requirements/<project>/`. They ask for the project name first. The next skill you run on the same project offers to reuse it, as long as the documents haven't changed. For example:

1. Monday: `/testkit:api-test-plan` for `orders-service` reads the PRD and spec, saves the requirements, and writes the API test plan.
2. A week later: `/testkit:create-testcase` for `orders-service` says "Found the requirements from 3 Nov (5 files, unchanged). Reuse them?" Yes → it goes straight to writing the test cases (UI, API or both, whatever the documents cover).
3. If a document changed in between, it tells you which one and offers to read them again.

Want only the reading, with no tests? Use `/testkit:read-requirements`.

Behind the scenes, the skills use helper agents. You don't call them yourself. Excel, Word and PowerPoint files are first converted to CSV and Markdown (with their pictures) by a small script in the plugin; Claude Code asks you before it runs.

| Agent | Job |
|---|---|
| [requirements-analyst](plugins/testkit/agents/requirements-analyst.md) | Reads all your documents and builds the requirements inventory: every requirement cited, plus contradictions and open questions. Read only. Shared by all the skills, so they agree on what the documents say |
| [doc-reader](plugins/testkit/agents/doc-reader.md) | Reads your documents, specs, code and images (screenshots, diagrams) and reports back. Read only: it can't run commands, change files or go online |

### skill-scan

| Skill | What it does | You type |
|---|---|---|
| [skill-scan](plugins/skill-scan/skills/skill-scan) | Security scan of AI agent skills, plugins and MCP configs before you install or share them. Gives a 0–100 risk score, a verdict and a report. Read only | `/skill-scan:skill-scan <folder>` |

Use it on your machine, or as a **pre-merge check on GitHub**: run `/skill-scan:skill-scan setup-ci` in your skills repo, and every PR gets a free automatic pattern check that blocks the merge until problems are fixed or accepted. No API key or secret is needed: the deep scan runs on your own machine with your Claude login. See [the skill-scan README](plugins/skill-scan/skills/skill-scan/README.md#pre-merge-check-on-pull-requests).

## Getting started

### 1. Install Claude Code

Follow the install steps on [claude.com/claude-code](https://claude.com/claude-code). You need a Claude account (Pro, Max, Team or Enterprise) or an Anthropic API key.

Check it works: open a terminal and type `claude`. You should see a prompt where you can type a message. Type `/exit` to leave.

### 2. Open Claude Code in your project

In the terminal, go to the folder you want to work in (for example your project's repo, or any folder if you only have documents), then start Claude Code:

```
cd ~/path/to/your/project
claude
```

Commands that start with `/` (like `/plugin`) are typed **inside** Claude Code, at its prompt, not in the normal terminal.

### 3. Install

Type these inside Claude Code, one at a time:

```
/plugin marketplace add ejlomuntad/qa-spectre
/plugin install testkit@qa-spectre
/plugin install skill-scan@qa-spectre
```

The first line tells Claude Code where to find these skills. The other two install them. Install only the ones you need.

Check it worked: type `/testkit` and you should see the four skills in the list.

To get updates later: `/plugin marketplace update qa-spectre`.

**Install the plugins, don't copy skill folders.** The testkit skills share files that live in the plugin (the requirements workflow, the agents, the converter), so a single skill folder copied on its own won't work; the skill tells you to install the plugin. skill-scan has no shared files, so it can also be copied to `~/.claude/skills/skill-scan/` and run as `/skill-scan`.

### 4. Run your first skill

For example, an API test plan:

1. Put your documents (PRD, user stories, API spec) in a folder named after your project: `~/Desktop/Testkit/qa-docs/<project>/`, e.g. `qa-docs/orders-service/`. Every testkit skill looks there. Excel, Word, PowerPoint and PDF files are fine. Export anything in Confluence or Google Docs to PDF, Word or Markdown first.
2. In Claude Code, type `/testkit:api-test-plan`.
3. Answer its questions, starting with the project name. When it's done, it tells you where the test plan was saved (by default `~/Desktop/Testkit/api-test-plan/<project>/`), and where the requirements it read are saved (`~/Desktop/Testkit/requirements/<project>/`).

Each skill's README explains what to give it and what you get back.

### Where everything is saved

All testkit skills use one main folder on your Desktop, with one subfolder per project. The first time, the skill tells you its full path:

```
~/Desktop/Testkit/
├── qa-docs/<project>/          ← put YOUR documents here (PRD, spec, Excel, screenshots)
├── requirements/<project>/     ← made by the skills: what they read, saved for reuse
├── api-test-plan/<project>/    ← API test plans (.md, and .html if asked)
├── test-cases/<project>/       ← test cases (.md summary + .csv)
└── api-audit/                     ← api-audit audits, bug evidence and ledgers
```

- The skills never change anything in `qa-docs/`: it's yours.
- `requirements/` is what lets a second skill reuse what the first one read. You can delete it any time; the skills will just read your documents again.
- To keep everything somewhere else (e.g. `~/Documents/Testkit`), set the main output folder in your [project rules](#project-rules). It must be inside your home folder.
- **On Windows**, "Desktop" is the one you actually see: if Windows moved it into OneDrive (`C:\Users\<name>\OneDrive\Desktop`), `Testkit` goes there. On a computer with no Desktop folder (e.g. a server), it's `~/Testkit`.
- skill-scan is a separate plugin and saves its reports to `~/Desktop/skill-scan-output/`.

### Which files can I use?

| File | Works? |
|---|---|
| PDF, Markdown, text, CSV, JSON, YAML | Yes, as they are |
| Screenshots, mockups and diagrams (`.png`, `.jpg`, `.gif`, `.webp`) | Yes. Claude looks at the picture: screens, labels, error messages, flows and arrows |
| Excel (`.xlsx`), Word (`.docx`), PowerPoint (`.pptx`) | Yes. They're converted for you, including the pictures inside them. Your files aren't changed |
| Old Office files (`.xls`, `.doc`, `.ppt`) or password-protected files | Save them as `.xlsx` / `.docx` / `.pptx` (or PDF) first |
| Confluence, Google Docs, Jira, Notion | Export to PDF, Word or Markdown first |
| Figma | Export first (below) |

**Figma designs:** Claude can't open Figma files or links. Export the screens instead:

1. In Figma, select the frames you need (hold Shift to pick several).
2. In the right panel, find **Export** and click **+**.
3. Choose **PNG** (one image per frame) or **PDF** (all frames in one file), then click **Export**.
4. Put the files in your project's docs folder (e.g. `~/Desktop/Testkit/qa-docs/orders-service/`) with the other documents.

Use clear frame names before exporting (e.g. `checkout-error-card-declined.png`): they show up as the source in your test cases.

*Advanced:* Figma also offers an MCP server that lets Claude read the design data directly (exact text, components, spacing). It needs a Figma plan with Dev Mode and is set up per user. See Figma's own guide for "Dev Mode MCP server". The skills work fine with exported images, so you don't need it.

**Works on macOS, Windows and Linux.** The skills have been tested on macOS. On Windows they use Claude Code's Git Bash. To convert Excel, Word and PowerPoint files you need Python 3 (`python3`, `python` or `py`); without it, the skill asks you to save those files as CSV or PDF first.

**Claude asks before it does things.** The first time a skill wants to run a command or write a file, Claude Code asks for permission. Read what it wants to do, then allow or deny. The skills never commit, push or post anything for you.

## Project rules

### What are they?

Project rules are a plain text notes file that tells the testkit skills about **your** project: things a new tester would need to be told on day one. For example:

- where your requirements, API spec and tests live;
- your domain terms ("an Order can't be edited after payment");
- units and formats ("money is in cents in the API");
- words you must or must not use in test cases;
- how your team's tickets look (Jira project key, required fields).

### Do I need them?

**No. They're optional.** Every skill works without them, using generic defaults. The output just shows `Project rules: none`.

Add them when you notice you keep telling the skill the same things, or when you want everyone on the team to get the same results.

### How to set them up

1. Open the template: [project-rules.example.md](plugins/testkit/project-rules.example.md).
2. Copy it to **one** of these places:
   - `<your project>/.claude/testkit/project-rules.md`: rules for one project. Commit it to the repo and your whole team uses the same rules.
   - `~/.claude/testkit/project-rules.md`: rules on your machine, for all your projects.
3. Fill in only the sections you need. Delete the rest.
4. Run a skill. The output shows `Project rules: <path>`, so you know they were picked up.

**Rules kept somewhere else?** Point to them with `rules=`, for example `/testkit:api-test-plan rules=docs/qa/project-rules.md`, or a GitHub link to a shared team repo: `rules=https://github.com/<org>/<repo>/blob/main/project-rules.md`.

If more than one exists, the skills use the first of: `rules=`, then the project's `.claude/testkit/project-rules.md`, then the one in your home folder.

Keep secrets (passwords, tokens) out of project rules. It's plain text, and the skills quote from it.

## License

[MIT](LICENSE)
