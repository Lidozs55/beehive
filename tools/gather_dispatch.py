#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""章派发素材一把抓：给主代理生成"本章参数"块，替代多次零散grep。
用法：python tools/gather_dispatch.py P007
只读，不写任何文件。"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read(p):
    return (ROOT / p).read_text(encoding="utf-8")


def main(pid):
    num = int(pid[1:])
    prev = f"P{num-1:03d}"
    out = [f"## 本章参数 · {pid}"]

    # 1 计划条目
    plan = json.loads(read("state/publishing-plan.json"))
    ent = next((e for e in plan if e.get("id") == pid), None)
    if ent:
        out.append(f"- 计划条目：单元{ent.get('unit')} 目标{ent.get('target_chars')}字 | 事件：{ent.get('event')}")
    else:
        out.append(f"- ⚠ {pid} 不在 publishing-plan.json！")

    # 2 场景卡（chapters/ 与 arcs/ 全量搜索）
    card = None
    cardfile = None
    card_files = sorted((ROOT / "chapters").glob("*.md")) + sorted((ROOT / "arcs").glob("*.md"))
    for f in card_files:
        text = f.read_text(encoding="utf-8")
        m = re.search(rf"(?ms)^##\s*{pid}\b.*?(?=^##\s|\Z)", text)
        if m:
            card, cardfile = m.group(0).strip(), f.name
            break
    if card:
        out.append(f"- 场景卡（{cardfile}，逐字照贴进简报）：\n{card}")
    else:
        out.append(f"- ⚠ 未找到 '## {pid}' 场景卡标题，需人工在 chapters/ arcs/ 定位")

    # 3 established-facts：本章条目行号 + 建议阅读区间
    ef_lines = read("state/established-facts.md").splitlines()
    hits = [i + 1 for i, l in enumerate(ef_lines) if f"（{pid}）" in l]
    if hits:
        lo, hi = max(1, hits[0] - 6), min(len(ef_lines), hits[-1] + 6)
        out.append(f"- established-facts：本章条目在第{hits}行 → 简报填阅读区间 第{lo}-{hi}行")
    else:
        out.append("- established-facts：本章无既有条目（新章），简报填'通读文件头部规则+上一章区间'")

    # 4 timeline-log 本章行（逐字引用，作时间锚）
    tl = read("state/timeline-log.md").splitlines()
    trows = [(i + 1, l) for i, l in enumerate(tl) if re.search(rf"\|\s*{pid}\s*\|", l)]
    if trows:
        for i, l in trows:
            out.append(f"- timeline-log 第{i}行（照贴）：{l.strip()}")
    else:
        out.append(f"- ⚠ timeline-log 无 {pid} 行（新章，回执提案登记）")

    # 5 summaries 节点行号区间（只给区间，不给内容）
    sm = read("state/summaries.md").splitlines()
    heads = [(i + 1, l) for i, l in enumerate(sm) if re.match(r"^## P\d{3}", l)]

    def node_span(p):
        for j, (ln, h) in enumerate(heads):
            if h.startswith(f"## {p}"):
                end = heads[j + 1][0] - 1 if j + 1 < len(heads) else len(sm)
                return ln, end
        return None

    cur, prv = node_span(pid), node_span(prev)
    if cur and prv:
        out.append(f"- summaries：本章节点 第{cur[0]}-{cur[1]}行（要点勾稽清单）；上一章节点 第{prv[0]}-{prv[1]}行 → 简报填区间 第{prv[0]}-{cur[1]}行")
    elif cur:
        out.append(f"- summaries：本章节点 第{cur[0]}-{cur[1]}行（无上一章节点）")
    elif prv:
        out.append(f"- summaries：无本章节点；上一章节点 第{prv[0]}-{prv[1]}行")
    else:
        out.append("- ⚠ summaries 无本章也无上一章节点")

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
    out.append(f"- 上一章文件：{prevf[0].name if prevf else f'⚠ {prev} 缺失！'}")

    print("\n".join(out))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python tools/gather_dispatch.py P0XX")
        sys.exit(1)
    main(sys.argv[1])
