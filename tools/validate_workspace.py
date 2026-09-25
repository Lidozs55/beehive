#!/usr/bin/env python3
"""Validate the v2 planning baseline and its document boundaries."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
checks = []


def check(name, condition, details=""):
    checks.append({"name": name, "passed": bool(condition), "details": details})


def main():
    plan = json.loads((ROOT / "state/plan.json").read_text(encoding="utf-8"))
    publishing = json.loads((ROOT / "state/publishing-plan.json").read_text(encoding="utf-8"))
    check("three_volume_plan", len(plan.get("units", [])) == 117)
    check("publish_plan", len(publishing) == 351)

    cards = sorted((ROOT / "chapters/写作卡").glob("P*.md"))
    check("no_legacy_cards", not cards, "v2 重启前不应存在旧 P 卡")
    bodies = sorted((ROOT / "正文").glob("*.md"))
    check("no_legacy_prose", not bodies, "v2 重启前不应存在旧正文")

    for path in [
        "00-项目总览与文档职能.md",
        "chapters/00-总大纲.md",
        "chapters/写作卡/00-卡片规范.md",
        "meta/派发模板.md",
        "state/handoff.md",
        "state/established-facts.md",
        "state/character-state.md",
        "state/timeline-log.md",
        "state/next-hook.md",
        "state/summaries-上卷.md",
        "state/summaries-中卷.md",
        "state/summaries-下卷.md",
    ]:
        check(f"required_{path}", (ROOT / path).exists())

    handoff = (ROOT / "state/handoff.md").read_text(encoding="utf-8")
    check("dispatch_paused", "v2_dispatch: paused" in handoff)
    for name in ("established-facts.md", "character-state.md", "timeline-log.md", "next-hook.md"):
        text = (ROOT / "state" / name).read_text(encoding="utf-8")
        check(f"empty_{name}", "当前没有 v2" in text)

    report = {"scope": "v2 restart baseline", "checks": checks,
              "passed": sum(x["passed"] for x in checks), "total": len(checks)}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] == report["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
