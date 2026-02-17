#!/usr/bin/env python3
"""
CasperVPN Dashboard Builder
Injects data.json inline into index.html so it works via file:// protocol.

Usage: python3 build_dashboard.py
Run this after any department updates data.json.
"""
import json, os

DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(DIR, 'data.json')) as f:
    data = json.load(f)

with open(os.path.join(DIR, 'index.html')) as f:
    html = f.read()

# Find and replace the INLINE_DATA constant
inline_json = json.dumps(data, ensure_ascii=True)
marker_start = 'const INLINE_DATA = '
marker_end = ';\n\nasync function loadData'

start_idx = html.index(marker_start)
end_idx = html.index(marker_end)

html = html[:start_idx] + marker_start + inline_json + html[end_idx:]

with open(os.path.join(DIR, 'index.html'), 'w') as f:
    f.write(html)

# Calculate stats
tw = sum(t['weight'] for t in data['tasks'])
ws = sum(t['weight'] * (t['progress']/100) for t in data['tasks'])
overall = round((ws/tw)*100) if tw > 0 else 0
blocked = [t['name'] for t in data['tasks'] if t.get('blocked')]

print(f"Dashboard rebuilt — {len(data['tasks'])} tasks, {overall}% overall, {len(blocked)} blocked")
print(f"File: {os.path.join(DIR, 'index.html')} ({os.path.getsize(os.path.join(DIR, 'index.html')):,} bytes)")
