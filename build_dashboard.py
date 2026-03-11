#!/usr/bin/env python3
"""
CasperVPN Dashboard Builder (Safe Edition)
Injects data.json inline into index.html using LINE-BY-LINE replacement.

SAFETY: Never use marker-based string splicing. Always find the exact
'const INLINE_DATA' line and replace only that line.

Usage: python3 build_dashboard.py
Run this after any department updates data.json.
"""
import json, os, sys

DIR = os.path.dirname(os.path.abspath(__file__))

# Load data.json
with open(os.path.join(DIR, "data.json")) as f:
    data = json.load(f)

# Load index.html
html_path = os.path.join(DIR, "index.html")
with open(html_path) as f:
    html = f.read()

# SAFETY CHECK: must be real HTML
if not html.strip().startswith("<!DOCTYPE") and not html.strip().startswith("<html"):
    print("ABORT: index.html is corrupted (not HTML). Skipping rebuild.")
    sys.exit(1)

# Line-by-line replacement — find the INLINE_DATA line and replace ONLY that line
inline_json = json.dumps(data, ensure_ascii=True)
lines = html.split("\n")
replaced = False
for i, line in enumerate(lines):
    if "const INLINE_DATA" in line and not line.strip().startswith("//"):
        lines[i] = "const INLINE_DATA = " + inline_json + ";"
        replaced = True
        break

if not replaced:
    print("ABORT: 'const INLINE_DATA' marker not found in index.html.")
    sys.exit(1)

new_html = "\n".join(lines)

# SAFETY CHECK: output must still be HTML
if not new_html.strip().startswith("<!DOCTYPE") and not new_html.strip().startswith("<html"):
    print("ABORT: rebuild produced non-HTML output. Skipping write.")
    sys.exit(1)

with open(html_path, "w") as f:
    f.write(new_html)

task_count = len(data.get("tasks", []))
xd_count = len(data.get("crossDeptTasks", []))
print(f"Dashboard rebuilt: {task_count} tasks, {xd_count} cross-dept tasks baked into index.html")
