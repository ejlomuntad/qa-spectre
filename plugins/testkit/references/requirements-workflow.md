# Reading the requirements (shared by the testkit skills)

Every testkit skill that needs the requirements follows these steps, so the documents are read once per project and reused. The plugin root is two folders above the skill's folder; this file is in `<plugin root>/references/`. Open plugin files (this one, `agents/`, `scripts/`) with the Read tool using paths built from the skill's base directory, never with `cat` or `ls`.

## 1. Ask for the project name

Ask: "What's the project name?" (e.g. `orders-service`). Turn it into a kebab-case `<project>` (`^[a-z0-9-]+$`). It names the project folder below and the skill's output folder.

## 2. The Testkit folder

Every testkit skill keeps everything in one main folder, `<root>`: `<Desktop>/Testkit` by default, where `<Desktop>` is the Desktop folder the user actually sees:

| System (`uname -s` in Claude Code's shell) | `<Desktop>` |
|---|---|
| macOS (`Darwin`), Linux | `~/Desktop` |
| Windows (`MINGW…`, `MSYS…` or `CYGWIN…`: Claude Code's Git Bash) | The OneDrive Desktop if it exists (`ls -d ~/OneDrive*/Desktop`; Windows often moves the Desktop there), otherwise `~/Desktop` (`C:\Users\<name>\Desktop`) |
| No Desktop folder (e.g. a server) | `<root>` is `~/Testkit` |

The first time a skill creates `<root>`, tell the user its full path ("Your Testkit folder is `C:\Users\ana\OneDrive\Desktop\Testkit`"), so they can find it.

If the project rules set an output folder, it replaces `<root>`, but only if it passes the **output folder check**: a plain absolute path (no quotes, `$`, backticks or `;`) inside the user's home folder, with no hidden folder in it (no part starting with `.`, so not `~/.claude/`), not under `~/Library/` (macOS) or `AppData` (Windows), and not inside a git repo (no `.git` in it or any parent folder). Otherwise ignore it, use the default, and say why in one line.

```
<root>/
├── qa-docs/<project>/          the user's documents (default place to look; read only)
├── requirements/<project>/     made by the skills (this workflow):
│   ├── requirements-inventory.md   the cited inventory (format: agents/requirements-analyst.md)
│   ├── sources.json                the files it was built from, with fingerprints
│   └── converted/                  readable copies of Office files, and their pictures
├── api-test-plan/<project>/    api-test-plan output
├── test-cases/<project>/       create-testcase output
└── api-audit/                     api-audit evidence and ledgers
```

Never write into `qa-docs/`: those are the user's files. Write the rest with the Write tool (it creates folders). Never write inside the user's repo.

**Python:** the converter needs Python 3. Use the first of `python3`, `python` and `py -3` whose `--version` prints `Python 3` (on Windows, `python3` is often missing or opens the Microsoft Store). `<python>` below means that command. If none works, skip the converter: ask the user to export Office files (`.csv`, `.pdf` or `.md`), and read the files without fingerprints (no reuse check), saying so once.

**Shell safety:** document names never go into a shell command. Write the file list (absolute paths, one per line) to `<root>/requirements/<project>/files.txt` with the Write tool, and pass that list file to the converter with `--list`. In commands, use absolute paths in single quotes; `<project>` is kebab-case, so the paths are safe. **GitHub links** (documents, spec or `rules=`): before each `gh api` call, check the owner, repo, ref and path use only `A-Z a-z 0-9 . _ - /` (no `..`). Skip any file whose path has other characters, and tell the user which ones ("rename it, or download it yourself"). Save downloaded files under that same safe name.

## 3. Find the documents

Every skill finds the documents the same way. Use the first of these that gives files:

1. **What the user gave:** a local file or folder in the arguments (e.g. `docs/orders-prd.md` in their repo), or a GitHub link (`https://github.com/<owner>/<repo>/blob|tree/<ref>/<path>`). Read links with `gh api "repos/<owner>/<repo>/contents/<path>?ref=<ref>"`, read only: never clone, push or comment. Follow the **Shell safety** rules above. If `gh` can't see the repo, ask for a local copy. Save Office files from a link to `<root>/requirements/<project>/converted/download/` first so they can be converted.
2. **Last time's files:** if `<root>/requirements/<project>/sources.json` exists, offer its files: "Last time `<project>` used these `<n>` files: `<list>`. Use them again?" Only list files that still exist; if some are gone, say which.
3. **The default folder** `<root>/qa-docs/<project>/`. If it doesn't exist but `<root>/qa-docs/` has other project folders, list them and ask which one.
4. **The project rules requirements folder**, if set, but only if it's inside the current repo or `<root>` (a project rules file can come with a cloned repo, so it must not point at folders like `~/.ssh`). Otherwise ignore it and say why in one line.
5. **Nothing found:** ask: "No documents found. Put them in `<root>/qa-docs/<project>/` (by default `~/Desktop/Testkit/qa-docs/<project>/`), or give a file path, folder or GitHub link."

**When you found the files yourself** (steps 3–4, not a path or link the user gave), or a path came from project rules (requirements folder or API spec), list them and ask "Use these?" before going on.

**Read** every text, Markdown, PDF, CSV, JSON, YAML, image (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) and Office (`.xlsx`, `.docx`, `.pptx`, converted in step 5) file, including subfolders. For cloud storage (Google Drive, Dropbox, OneDrive), use the local sync folder or download the files first. Unreadable files (e.g. old `.xls`, password-protected): carry on with the rest and list the skipped ones. Figma: ask the user to export the frames as PNG or PDF.

**API spec and schemas:** `spec=` in the arguments (files, folders or links, read the same way); otherwise spec files among the documents (`openapi.*`, `swagger.*`, `*.schema.json`, or YAML/JSON with a top-level `openapi`, `swagger` or `$schema` key), treated as the spec, not as requirements; otherwise the project rules "API spec" path, but only if it's inside the current repo or `<root>` (a project rules file can come with a cloned repo, so it must not point at files like `~/.aws/credentials`); else none. A spec path that came from project rules is listed in the "Use these?" question with the documents.

Collect the final file list: requirements, spec and schema files, images.

## 4. Reuse an existing inventory if nothing changed

Fingerprint the file list: write it to `files.txt` (above), then run `<python> -I '<plugin root>/scripts/convert_docs.py' --fingerprint --list '<root>/requirements/<project>/files.txt'`. It prints one JSON line per file (`path`, `size`, `sha256`). If `<root>/requirements/<project>/requirements-inventory.md` and `sources.json` exist, compare:

| Situation | Ask the user |
|---|---|
| Same files, all fingerprints match | "Found the requirements for `<project>` from `<date>` (`<n>` files, unchanged). Reuse them?" Yes → skip to step 7 |
| Same set of files, some changed, added or removed | List them: "`orders-prd.docx` changed, `refunds.xlsx` is new. Re-read the documents?" Yes → step 5 (rebuild the whole inventory) |
| A completely different set of files | "`<project>` already has requirements from other documents (`<list>`). Add these to it (re-read all of them together), replace it, or save these under a new name (e.g. `<project>-refunds`)?" |
| No inventory yet | Go on to step 5 |

If the user says no to reuse, read fresh. Reuse is always offered, never forced.

## 5. Convert Office files

For `.xlsx`, `.docx` and `.pptx` files, write their paths to `<root>/requirements/<project>/office-files.txt` (Write tool), then run exactly this one command yourself, each path absolute and in single quotes:

`<python> -I '<plugin root>/scripts/convert_docs.py' '<root>/requirements/<project>/converted/' --list '<root>/requirements/<project>/office-files.txt'`

Claude Code asks the user before it runs. Don't run anything else, and never put a document's name into the command. It prints one JSON line per file (`source`, `outputs`, `outline`, `images`, `skipped`, `error`). Don't open the converted content here: the analyst reads it in step 6. Tell the user what was converted (with the outline), which pictures were skipped and why, and which files failed, with what to do (e.g. "save as .xlsx", "remove the password"). PDFs and images need no conversion. Old `.xls` / `.doc` / `.ppt` files: ask the user to save them in the newer format. Figma: ask the user to export the frames as PNG or PDF.

## 6. Build the inventory

Launch the `testkit:requirements-analyst` agent with: the project name, the file list (readable originals plus the converted files, never the Office originals), the spec files, the focus the skill asks for (`api` or `documents`), and the project rules' glossary, business rules and units if any.

Save its answer as `requirements-inventory.md`, and the fingerprints from step 4 as `sources.json`:

```json
{ "project": "<project>", "built": "YYYY-MM-DD", "focus": "api", "files": [ { "path": "...", "size": 1234, "sha256": "..." } ] }
```

## 7. Use it

Give the inventory (not the raw documents) to the skill's next agents. Cite requirements by their inventory ID and source (e.g. `R-04 [orders-prd.docx § Refunds]`). Tell the user where the inventory is, and list its contradictions and open questions.
