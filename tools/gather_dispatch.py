#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""章派发素材一把抓：给主代理生成"本章参数"块，替代多次零散grep。
用法：python tools/gather_dispatch.py P007
只读，不写任何文件。"""
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def workflow_open():
    handoff = (ROOT / "state" / "handoff.md").read_text(encoding="utf-8")
    return "v2_dispatch: open" in handoff


def main(pid):
    if not workflow_open():
        print("[BLOCKED] v2 派发尚未开启；当前旧轮次材料不得进入派发链。", file=sys.stderr)
        return 2
    num = int(pid[1:])
    prev = f"P{num-1:03d}"
    out = [f"## 本章参数 · {pid}"]

    # 1 计划条目
    plan = json.loads(read("state/publishing-plan.json"))
    ent = next((e for e in plan if e.get("id") == pid), None)
    if ent:
        out.append(f"- 计划条目：单元{ent.get('unit')} 目标{ent.get('target_chars')}字 | 事件：{ent.get('event')}")
    else:
        out.append(f"- [WARN] {pid} 不在 publishing-plan.json！")

    # 2 写作卡（chapters/写作卡/ 每章一卡优先；chapters/ 与 arcs/ 兜底）
    card = None
    cardfile = None
    card_files = (sorted((ROOT / "chapters" / "写作卡").glob("*.md"))
                  + sorted((ROOT / "chapters").glob("*.md"))
                  + sorted((ROOT / "arcs").glob("*.md")))
    for f in card_files:
        text = f.read_text(encoding="utf-8")
        m = re.search(rf"(?ms)^##\s*{pid}\b.*?(?=^##\s|\Z)", text)
        if m:
            card, cardfile = m.group(0).strip(), f.name
            break
    if card:
        out.append(f"- 写作卡（{cardfile}，逐字照贴进简报）：\n{card}")
    else:
        out.append(f"- [WARN] {pid} 无写作卡（chapters/写作卡/{pid}.md 缺失）")

    # 3 established-facts：本章条目行号 + 建议阅读区间
    ef_lines = read("state/established-facts.md").splitlines()
    hits = [i + 1 for i, l in enumerate(ef_lines) if f"（{pid}）" in l]
    if hits:
        # Include prior context, but never leak later planned chapters into a dispatch.
        lo, hi = max(1, hits[0] - 6), hits[-1]
        out.append(f"- established-facts：本章条目在第{hits}行 → 简报填阅读区间 第{lo}-{hi}行（止于本章最后一条，勿向后读取未来章）")
    else:
        out.append("- established-facts：本章无既有条目（新章），简报填'通读文件头部规则+上一章区间'")

    # 4 timeline-log 本章行（逐字引用，作时间锚）
    tl = read("state/timeline-log.md").splitlines()
    trows = [(i + 1, l) for i, l in enumerate(tl) if re.search(rf"{pid}(?!\d)", l)]
    if trows:
        for i, l in trows:
            out.append(f"- timeline-log 第{i}行（照贴）：{l.strip()}")
    else:
        out.append(f"- [WARN] timeline-log 无 {pid} 行（新章，回执提案登记）")

    # 5 summaries 节点位置（上/中/下三卷）；代理用 slice_summaries.py 提取，不全量读取。
    volumes = [p for v in ("上卷", "中卷", "下卷")
               if (p := ROOT / "state" / f"summaries-{v}.md").exists()]
    legacy = ROOT / "state" / "summaries.md"
    if legacy.exists():
        volumes.append(legacy)

    def node_span(path, target):
        lines = path.read_text(encoding="utf-8").splitlines()
        heads = [(i, l) for i, l in enumerate(lines) if re.match(r"^## P\d{3}", l)]
        for j, (idx, h) in enumerate(heads):
            if h.startswith(f"## {target}"):
                end = heads[j + 1][0] if j + 1 < len(heads) else len(lines)
                return idx + 1, end
        return None

    cur = prv = None
    curvol = prvvol = ""
    for p in volumes:
        if cur is None:
            span = node_span(p, pid)
            if span:
                cur, curvol = span, p.name
        if prv is None:
            span = node_span(p, prev)
            if span:
                prv, prvvol = span, p.name
    if cur and prv:
        out.append(f"- summaries：运行 python tools/slice_summaries.py {prev} {pid}（定位：上一章{prvvol}L{prv[0]}-{prv[1]}，本章{curvol}L{cur[0]}-{cur[1]}）")
    elif cur:
        out.append(f"- summaries：运行 python tools/slice_summaries.py {pid}（本章{curvol}L{cur[0]}-{cur[1]}，无上一章节点）")
    elif prv:
        out.append(f"- summaries：本章无节点；运行 python tools/slice_summaries.py {prev} 读取上一章{prvvol}L{prv[0]}-{prv[1]}")
    else:
        out.append("- [WARN] summaries 无本章也无上一章节点")

    # 6 到期钩子（next-hook 命中行，逐字引用）
    nh = read("state/next-hook.md").splitlines()
    hrows = [(i + 1, l.strip()) for i, l in enumerate(nh) if pid in l and l.strip().startswith("|")]
    if hrows:
        rows = "；".join(f"L{i}:{l}" for i, l in hrows)
        out.append(f"- 到期钩子（照贴）：{rows}")
    else:
        out.append("- 到期钩子：next-hook 无精确命中行，主代理自行判断活跃表中应动项")

    # 7 上一章文件
    prevf = sorted((ROOT / "正文").glob(f"{prev}-*.md"))
    out.append(f"- 上一章文件：{prevf[0].name if prevf else f'[WARN] {prev} 缺失！'}")

    print("\n".join(out))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python tools/gather_dispatch.py P0XX")
        sys.exit(1)
    sys.exit(main(sys.argv[1]))
