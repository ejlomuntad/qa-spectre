#!/usr/bin/env python3
"""Turn Excel (.xlsx), Word (.docx) and PowerPoint (.pptx) files into text the testkit agents can read.

    python3 convert_docs.py <out_dir> --list <list file>
    python3 convert_docs.py --fingerprint --list <list file>    size + SHA-256 per file, to tell if it changed

<list file> is a text file with one path per line. The skills write it with the Write tool, so
document names never appear in a shell command. (Paths can also follow on the command line, for
manual use: convert_docs.py <out_dir> <file> ...)

- .xlsx -> one CSV per sheet: <out_dir>/<file stem>__<sheet>.csv
- .docx -> Markdown: <out_dir>/<file stem>.md (paragraphs, headings, tables)
- .pptx -> Markdown: <out_dir>/<file stem>.md (one section per slide, with speaker notes)

Embedded pictures (screenshots, diagrams, mockups) are saved to <out_dir>/<file stem>__images/,
and the Markdown gets an [image: <path>] marker where each one appears, so an agent can look at
it in context. Formats Claude can't view (EMF, WMF, TIFF, SVG ...) are listed as skipped.

Prints one JSON line per input: {"source", "outputs", "outline", "images", "skipped", "error"}.
"outline" says what came out without anyone reading it: rows per CSV, headings or slides per
Markdown file. Exit code 0 even if a file fails, so the skill can report it and carry on.

Standard library only. Read only on the inputs: output goes to <out_dir>, never next to the
source. Formulas come out as their last saved values; charts and comments are skipped.
Old .xls, .doc and .ppt files aren't supported: save them in the newer format (or CSV / PDF) first.
"""
import csv
import hashlib
import json
import os
import posixpath
import re
import sys
import xml.etree.ElementTree as ET
import zipfile

MAX_FILE = 50 * 1024 * 1024        # compressed input
MAX_ENTRY = 100 * 1024 * 1024      # any single uncompressed part (zip-bomb guard)
MAX_IMAGE = 20 * 1024 * 1024       # per picture
MAX_IMAGES = 200                   # per file
MAX_TOTAL = 500 * 1024 * 1024      # all parts of one file together, uncompressed
VIEWABLE = {".png", ".jpg", ".jpeg", ".gif", ".webp"}
NS = {
    "s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
}


def open_package(path):
    z = zipfile.ZipFile(path)
    if sum(i.file_size for i in z.infolist()) > MAX_TOTAL:
        z.close()
        raise ValueError("file is over 500 MB when unpacked (refused)")
    return z


def read_xml(z, name):
    info = z.getinfo(name)
    if info.file_size > MAX_ENTRY:
        raise ValueError(f"{name} is too large when unpacked")
    data = z.read(name)
    # Office XML is UTF-8. A UTF-16 part could hide a DTD from the byte check below.
    if data[:2] in (b"\xff\xfe", b"\xfe\xff"):
        raise ValueError(f"{name} is UTF-16 encoded (refused)")
    if b"<!DOCTYPE" in data or b"<!ENTITY" in data:
        raise ValueError(f"{name} contains DTD/entity declarations (refused)")
    return ET.fromstring(data)


def defuse(text):
    """Document text must never look like one of our own markers: a fake
    "[image: ~/.ssh/id_rsa]" in a document could otherwise make an agent read that file."""
    return re.sub(r"\[\s*image\s*:", "[image-text:", text, flags=re.I)


def safe_name(text):
    return re.sub(r"[^A-Za-z0-9._-]+", "_", text).strip("_") or "sheet"


def load_rels(z, rels_path):
    """Relationship id -> resolved part name inside the package."""
    if rels_path not in z.namelist():
        return {}
    base = posixpath.dirname(posixpath.dirname(rels_path))  # .../_rels/x.rels -> ...
    out = {}
    for r in read_xml(z, rels_path).findall("rel:Relationship", NS):
        target = r.get("Target", "")
        if r.get("TargetMode") == "External":
            continue
        part = target.lstrip("/") if target.startswith("/") else posixpath.normpath(posixpath.join(base, target))
        out[r.get("Id")] = part
    return out


class Images:
    """Saves embedded pictures under <out_dir>/<stem>__images/ and remembers what it skipped."""

    def __init__(self, z, out_dir, stem):
        self.z, self.dir = z, os.path.join(out_dir, f"{stem}__images")
        self.saved, self.skipped = {}, []

    def save(self, part):
        if part in self.saved:
            return self.saved[part]
        name = posixpath.basename(part)
        ext = os.path.splitext(name)[1].lower()
        if part not in self.z.namelist():
            return None
        if ext not in VIEWABLE:
            self.skipped.append(f"{name}: {ext or 'unknown'} pictures can't be viewed")
            self.saved[part] = None
            return None
        if len([v for v in self.saved.values() if v]) >= MAX_IMAGES:
            self.skipped.append(f"{name}: over {MAX_IMAGES} pictures in one file")
            self.saved[part] = None
            return None
        if self.z.getinfo(part).file_size > MAX_IMAGE:
            self.skipped.append(f"{name}: picture over 20 MB")
            self.saved[part] = None
            return None
        os.makedirs(self.dir, exist_ok=True)
        out = os.path.join(self.dir, safe_name(name))
        with open(out, "wb") as f:
            f.write(self.z.read(part))
        self.saved[part] = out
        return out

    def markers(self, el, rels):
        found = []
        for blip in el.iter(f"{{{NS['a']}}}blip"):
            path = self.save(rels.get(blip.get(f"{{{NS['r']}}}embed"), ""))
            if path:
                found.append(f"[image: {path}]")
        return found

    def saved_list(self):
        return [v for v in self.saved.values() if v]


def col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + ord(ch) - 64
    return n - 1


def convert_xlsx(path, out_dir):
    outputs = []
    with open_package(path) as z:
        images = Images(z, out_dir, safe_name(os.path.splitext(os.path.basename(path))[0]))
        for part in sorted(n for n in z.namelist() if n.startswith("xl/media/")):
            images.save(part)  # pictures in a sheet have no cell position worth keeping
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in read_xml(z, "xl/sharedStrings.xml").findall("s:si", NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{NS['s']}}}t")))
        book = read_xml(z, "xl/workbook.xml")
        rels = read_xml(z, "xl/_rels/workbook.xml.rels")
        targets = {r.get("Id"): r.get("Target") for r in rels.findall("rel:Relationship", NS)}
        stem = safe_name(os.path.splitext(os.path.basename(path))[0])
        for sheet in book.findall("s:sheets/s:sheet", NS):
            target = targets.get(sheet.get(f"{{{NS['r']}}}id"), "")
            part = target.lstrip("/") if target.startswith("/") else "xl/" + target
            part = os.path.normpath(part).replace(os.sep, "/")
            if not part.startswith("xl/") or part not in z.namelist():
                continue
            rows = []
            for row in read_xml(z, part).iter(f"{{{NS['s']}}}row"):
                cells = {}
                for c in row.findall("s:c", NS):
                    ref, kind = c.get("r", ""), c.get("t")
                    v = c.find("s:v", NS)
                    if kind == "s" and v is not None:
                        value = shared[int(v.text)] if v.text and int(v.text) < len(shared) else ""
                    elif kind == "inlineStr":
                        value = "".join(t.text or "" for t in c.iter(f"{{{NS['s']}}}t"))
                    elif kind == "b" and v is not None:
                        value = "TRUE" if v.text == "1" else "FALSE"
                    else:
                        value = v.text if v is not None and v.text is not None else ""
                    idx = col_index(ref) if ref else len(cells)
                    cells[idx] = defuse(value)
                if cells:
                    rows.append([cells.get(i, "") for i in range(max(cells) + 1)])
            out = os.path.join(out_dir, f"{stem}__{safe_name(sheet.get('name', 'sheet'))}.csv")
            with open(out, "w", newline="", encoding="utf-8") as f:
                csv.writer(f).writerows(rows)
            outputs.append(out)
    return outputs, images


def convert_docx(path, out_dir):
    w = f"{{{NS['w']}}}"
    stem = safe_name(os.path.splitext(os.path.basename(path))[0])
    z = open_package(path)
    body = read_xml(z, "word/document.xml").find(f"{w}body")
    rels = load_rels(z, "word/_rels/document.xml.rels")
    images = Images(z, out_dir, stem)
    lines = []

    def para_text(p):
        text = defuse("".join(t.text or "" for t in p.iter(f"{w}t")).strip())
        return " ".join([text] + images.markers(p, rels)).strip()

    for el in list(body) if body is not None else []:
        if el.tag == f"{w}p":
            text = para_text(el)
            if not text:
                continue
            style = el.find(f"{w}pPr/{w}pStyle")
            level = re.match(r"Heading(\d)", style.get(f"{w}val", "")) if style is not None else None
            lines.append(("#" * int(level.group(1)) + " " if level else "") + text)
            lines.append("")
        elif el.tag == f"{w}tbl":
            rows = []
            for tr in el.iter(f"{w}tr"):
                rows.append([" ".join(para_text(p) for p in tc.iter(f"{w}p")).replace("|", "\\|")
                             for tc in tr.findall(f"{w}tc")])
            if rows:
                width = max(len(r) for r in rows)
                rows = [r + [""] * (width - len(r)) for r in rows]
                lines.append("| " + " | ".join(rows[0]) + " |")
                lines.append("|" + "---|" * width)
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                lines.append("")
    z.close()
    out = os.path.join(out_dir, f"{stem}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")
    return [out], images


def convert_pptx(path, out_dir):
    a = f"{{{NS['a']}}}"
    stem = safe_name(os.path.splitext(os.path.basename(path))[0])
    with open_package(path) as z:
        images = Images(z, out_dir, stem)
        names = z.namelist()
        slides = sorted((n for n in names if re.fullmatch(r"ppt/slides/slide\d+\.xml", n)),
                        key=lambda n: int(re.search(r"(\d+)", n.rsplit("/", 1)[1]).group(1)))
        lines = []
        for i, name in enumerate(slides, 1):
            lines.append(f"## Slide {i}")
            slide = read_xml(z, name)
            for para in slide.iter(f"{a}p"):
                text = defuse("".join(t.text or "" for t in para.iter(f"{a}t")).strip())
                if text:
                    lines.append(text)
            rels = load_rels(z, f"ppt/slides/_rels/{name.rsplit('/', 1)[1]}.rels")
            lines += images.markers(slide, rels)
            notes = f"ppt/notesSlides/notesSlide{name.rsplit('slide', 1)[1]}"
            if notes in names:
                note_text = [("".join(t.text or "" for t in p.iter(f"{a}t"))).strip()
                             for p in read_xml(z, notes).iter(f"{a}p")]
                note_text = [defuse(t) for t in note_text if t and not t.isdigit()]
                if note_text:
                    lines.append("")
                    lines.append("Notes: " + " ".join(note_text))
            lines.append("")
    out = os.path.join(out_dir, f"{stem}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")
    return [out], images


def fingerprint(paths):
    for path in paths:
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for block in iter(lambda: f.read(1 << 20), b""):
                    h.update(block)
            print(json.dumps({"path": path, "size": os.path.getsize(path), "sha256": h.hexdigest()}))
        except OSError as e:
            print(json.dumps({"path": path, "error": str(e)}))


USAGE = "usage: convert_docs.py <out_dir> --list <list file>  |  --fingerprint --list <list file>"


def paths_from(args):
    """Paths after --list <file> (one per line), else the remaining arguments."""
    if args[:1] == ["--list"]:
        if len(args) != 2:
            sys.exit(USAGE)
        with open(args[1], encoding="utf-8") as f:
            return [line.rstrip("\r\n") for line in f if line.strip()]
    return args


def outline(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    if path.endswith(".csv"):
        return f"{os.path.basename(path)}: {text.count(chr(10))} rows"
    slides = len(re.findall(r"^## Slide \d+", text, re.M))
    if slides:
        return f"{os.path.basename(path)}: {slides} slides"
    return f"{os.path.basename(path)}: {len(re.findall(r'^#+ ', text, re.M))} headings, {text.count(chr(10))} lines"


def main():
    if sys.argv[1:2] == ["--fingerprint"]:
        files = paths_from(sys.argv[2:])
        if not files:
            sys.exit(USAGE)
        fingerprint(files)
        return
    if len(sys.argv) < 3:
        sys.exit(USAGE)
    out_dir = sys.argv[1]
    files = paths_from(sys.argv[2:])
    os.makedirs(out_dir, exist_ok=True)
    for path in files:
        result = {"source": path, "outputs": [], "outline": [], "images": [], "skipped": [], "error": None}
        try:
            ext = os.path.splitext(path)[1].lower()
            if os.path.getsize(path) > MAX_FILE:
                raise ValueError("file is over 50 MB")
            if ext == ".xlsx":
                result["outputs"], images = convert_xlsx(path, out_dir)
                result["images"], result["skipped"] = images.saved_list(), images.skipped
            elif ext == ".docx":
                result["outputs"], images = convert_docx(path, out_dir)
                result["images"], result["skipped"] = images.saved_list(), images.skipped
            elif ext == ".pptx":
                result["outputs"], images = convert_pptx(path, out_dir)
                result["images"], result["skipped"] = images.saved_list(), images.skipped
            elif ext in (".xls", ".doc", ".ppt"):
                raise ValueError(f"old {ext} format: save it as {ext}x (or CSV / PDF) first")
            else:
                raise ValueError(f"not an .xlsx, .docx or .pptx file: {ext or 'no extension'}")
            result["outline"] = [outline(o) for o in result["outputs"]]
        except (zipfile.BadZipFile, KeyError) as e:
            result["error"] = f"can't read it as an Office file ({e.__class__.__name__}). Is it password-protected or damaged?"
        except Exception as e:  # report and carry on with the other files
            result["error"] = str(e)
        print(json.dumps(result))


if __name__ == "__main__":
    main()
