#!/usr/bin/env python3
"""Read an API test run report into one common format, whatever tool produced it.

    python3 read_results.py <report> <out.json>

<report> is either:
- a newman JSON report (Postman: `--reporters json --reporter-json-export <file>`), or
- a JUnit XML report, which most test tools can write: Bruno, Insomnia (inso), REST Assured
  and Karate (Maven/Gradle), pytest (`--junitxml`), Jest (jest-junit), Playwright, k6, newman.

The format is detected from the file. <out.json> gets:

    {"source", "format": "newman" | "junit",
     "summary": {"tests", "passed", "failed", "errors", "skipped"},
     "results": [{"suite", "name", "status": "passed" | "failed" | "error" | "skipped",
                  "message", "request": {...}, "response": {...}}]}

`request` and `response` (method, URL, status code, body) are only in newman reports; JUnit
reports don't carry them. Response bodies are cut to 4,000 characters. The summary line is also
printed. Standard library only; refuses files over 50 MB, DTD/entity declarations and UTF-16 XML.
"""
import json
import os
import sys
import xml.etree.ElementTree as ET

MAX_FILE = 50 * 1024 * 1024
MAX_BODY = 4000


def read_newman(data):
    run = data.get("run", {})
    folders = {}

    def walk(items, path):
        for it in items or []:
            if "item" in it:    # a folder
                walk(it["item"], path + [it.get("name", "")])
            else:
                folders[it.get("id")] = "/".join(p for p in path if p)

    walk(data.get("collection", {}).get("item"), [])
    results = []
    for ex in run.get("executions", []):
        item = ex.get("item", {})
        req = ex.get("request", {}) or {}
        url = req.get("url", "")
        if isinstance(url, dict):
            url = url.get("raw") or ("/".join(url.get("host", [])) + "/" + "/".join(url.get("path", [])))
        resp = ex.get("response", {}) or {}
        body = resp.get("stream", {}).get("data") if isinstance(resp.get("stream"), dict) else None
        if isinstance(body, list):
            body = bytes(b & 0xFF for b in body).decode("utf-8", "replace")
        common = {
            "suite": folders.get(item.get("id"), ""),
            "request": {"name": item.get("name", ""), "method": req.get("method", ""), "url": url},
            "response": {"status": resp.get("code"), "body": (body or "")[:MAX_BODY]},
        }
        assertions = ex.get("assertions") or []
        if ex.get("requestError"):
            results.append(dict(common, name=item.get("name", "") + " (request)", status="error",
                                message=str(ex["requestError"].get("message", "request failed"))))
        for a in assertions:
            err = a.get("error")
            status = "skipped" if a.get("skipped") else ("failed" if err else "passed")
            results.append(dict(common, name=f"{item.get('name', '')} › {a.get('assertion', '')}",
                                status=status, message=(err or {}).get("message", "")))
        if not assertions and not ex.get("requestError"):
            results.append(dict(common, name=item.get("name", "") + " (no assertions)", status="passed", message=""))
    return results


def read_junit(raw):
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        raise ValueError("UTF-16 XML (refused)")
    if b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        raise ValueError("XML with DTD/entity declarations (refused)")
    root = ET.fromstring(raw)
    results = []
    for case in root.iter("testcase"):
        status, message = "passed", ""
        for tag, st in (("failure", "failed"), ("error", "error"), ("skipped", "skipped")):
            el = case.find(tag)
            if el is not None:
                status = st
                message = (el.get("message") or (el.text or "")).strip()[:MAX_BODY]
                break
        results.append({"suite": case.get("classname", ""), "name": case.get("name", ""),
                        "status": status, "message": message, "request": {}, "response": {}})
    return results


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: read_results.py <report.json|report.xml> <out.json>")
    src, out = sys.argv[1], sys.argv[2]
    if os.path.getsize(src) > MAX_FILE:
        sys.exit("report is over 50 MB (refused)")
    with open(src, "rb") as f:
        raw = f.read()
    if raw[:2] in (b"\xff\xfe", b"\xfe\xff"):
        sys.exit("refused: UTF-16 report (save it as UTF-8)")
    text = raw.lstrip(b"\xef\xbb\xbf").lstrip()
    try:
        if text[:1] in (b"{", b"["):
            fmt, results = "newman", read_newman(json.loads(text.decode("utf-8")))
        elif text[:1] == b"<":
            fmt, results = "junit", read_junit(text)
        else:
            sys.exit("not a newman JSON or JUnit XML report")
    except (ValueError, ET.ParseError, AttributeError, TypeError) as e:
        sys.exit(f"refused or unreadable report: {e}")
    summary = {"tests": len(results)}
    for st in ("passed", "failed", "error", "skipped"):
        summary[st if st != "error" else "errors"] = sum(1 for r in results if r["status"] == st)
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"source": src, "format": fmt, "summary": summary, "results": results}, f, indent=1)
    print(json.dumps({"format": fmt, **summary}))


if __name__ == "__main__":
    main()
