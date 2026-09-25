#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Print selected chapter summaries without loading the full ledger.

Usage:
  python tools/slice_summaries.py P069 P070
  python tools/slice_summaries.py P051-P070
"""
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
VOLUMES = ("上卷", "中卷", "下卷")
PID_RE = re.compile(r"^P(\d{3})$")
RANGE_RE = re.compile(r"^P(\d{3})-P?(\d{3})$")
HEADING_RE = re.compile(r"^## (P\d{3})(?=\s|[（(【]|$)")


def workflow_open():
    handoff = (ROOT / "state" / "handoff.md").read_text(encoding="utf-8")
    return "v2_dispatch: open" in handoff


def summary_paths():
    if not workflow_open():
        return []
    paths = [ROOT / "state" / f"summaries-{v}.md" for v in VOLUMES]
    paths = [p for p in paths if p.exists()]
    legacy = ROOT / "state" / "summaries.md"
    if legacy.exists():
        paths.append(legacy)
    return paths


def requested_pids(args):
    numbers = []
    for arg in args:
        value = arg.upper()
        match = PID_RE.match(value)
        if match:
            numbers.append(int(match.group(1)))
            continue
        match = RANGE_RE.match(value)
        if match:
            start, end = map(int, match.groups())
            if start > end:
                raise ValueError(f"反向区间：{arg}")
            numbers.extend(range(start, end + 1))
            continue
        raise ValueError(f"无效章节参数：{arg}")
    return [f"P{number:03d}" for number in dict.fromkeys(numbers)]


def split_entries(text):
    lines = text.splitlines()
    heads = [(index, HEADING_RE.match(line).group(1)) for index, line in enumerate(lines) if HEADING_RE.match(line)]
    entries = {}
    for position, (start, pid) in enumerate(heads):
        end = heads[position + 1][0] if position + 1 < len(heads) else len(lines)
        entries.setdefault(pid, []).append("\n".join(lines[start:end]).rstrip())
    return entries


def main(args):
    if not workflow_open():
        print("[BLOCKED] v2 尚未开启；旧轮次 summaries 不可作为事实输入。", file=sys.stderr)
        return 4
    if not args:
        print("用法：python tools/slice_summaries.py P069 P070 或 P051-P070")
        return 1
    try:
        pids = requested_pids(args)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2

    entries = {}
    for path in summary_paths():
        for pid, blocks in split_entries(path.read_text(encoding="utf-8")).items():
            entries.setdefault(pid, []).extend(blocks)
    missing = [pid for pid in pids if pid not in entries]
    if missing:
        print(f"[WARN] 未找到摘要：{', '.join(missing)}", file=sys.stderr)

    blocks = [block for pid in pids for block in entries.get(pid, [])]
    if blocks:
        print("\n\n".join(blocks))
    return 0 if not missing else 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
