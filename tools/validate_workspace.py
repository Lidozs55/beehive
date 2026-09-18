#!/usr/bin/env python3
"""Finite structural/arithmetical checks for the Beehive planning overlay.
This is not a proof of literary quality or arbitrary future-plot consistency.
"""
import json
import math
import re
import sys
import subprocess
sys.dont_write_bytecode = True
from pathlib import Path
from urllib.parse import unquote
from check_population import calculate

ROOT=Path(__file__).resolve().parents[1]
checks=[]
def check(name,condition,details=""):
    checks.append({"name":name,"passed":bool(condition),"details":details})
def load(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

def main():
    plan=load("state/plan.json"); units=plan["units"]
    pub=load("state/publishing-plan.json")
    ledger=load("state/foreshadows.json"); timeline=load("state/timeline.json")
    trials=load("state/trials.json"); cards=load("state/opening-cards.json")
    ids=[u["id"] for u in units]; known=set(ids)
    check("unique_117_units",len(ids)==117 and len(known)==117)
    check("three_volume_counts",all(sum(x.startswith(p) for x in ids)==n for p,n in [("U",39),("M",36),("D",42)]))
    check("unit_sequences",ids==[f"{p}{i:02}" for p,n in [("U",39),("M",36),("D",42)] for i in range(1,n+1)])
    check("every_unit_three_nonempty_beats",all(len(u["beats"])==3 and all(len(b)>20 for b in u["beats"]) for u in units))
    check("every_unit_has_title_hook_time",all(u["title"] and u["hook"] and u["time"] for u in units))
    check("unit_budget_1131000",sum(u["target_chars"] for u in units)==1131000==plan["target_chars"])
    check("351_publish_chapters",len(pub)==351 and [p["id"] for p in pub]==[f"P{i:03}" for i in range(1,352)])
    check("publish_events_match_units",all(p["unit"]==units[i//3]["id"] and p["event"]==units[i//3]["beats"][i%3] for i,p in enumerate(pub)))
    check("publish_budget_matches",sum(p["target_chars"] for p in pub)==plan["target_chars"])
    check("18_opening_cards",len(cards)==18 and [c["id"] for c in cards]==[f"P{i:03}" for i in range(1,19)])
    check("opening_scene_cards_complete",all(len(c["scenes"])>=2 and all(c[k] for k in ["goal","knowledge","cost","hook"]) for c in cards))
    check("no_published_chapters",plan["published_chapters"]==0 and all(u["status"]=="planned" for u in units))
    fid=[x["id"] for x in ledger]; fset=set(fid)
    check("59_unique_promises",len(fid)==59==len(fset))
    check("43_main_16_seventh",fset=={f"F{i}" for i in range(1,44)}|{f"F-7-{i}" for i in range(1,17)})
    check("all_unit_clues_resolved",all(f in fset for u in units for f in u["clues"]))
    check("all_seeds_and_payoffs_exist",all(x["seed"] in known and all(y in known for y in x["payoff"]) for x in ledger))
    rank={u:i for i,u in enumerate(ids)}
    check("no_payoff_before_seed",all(rank[x["seed"]]<=min(rank[y] for y in x["payoff"]) for x in ledger))
    status_ok={chr(24453)+chr(31181),chr(24050)+chr(31181)}
    check("planted_status_legal",all(x["status"] in status_ok for x in ledger))
    check("planted_needs_seed_P",all(x.get("seed_P") for x in ledger if x["status"]==chr(24050)+chr(31181)))
    check("six_upper_trials",len(trials["upper"])==6)
    check("all_upper_rosters_six",all(len(t["roster"])==len(set(t["roster"]))==6 for t in trials["upper"]))
    check("all_upper_outcomes_partition",all(set(t["passed"]).isdisjoint(t["failed"]) and set(t["passed"])|set(t["failed"])==set(t["roster"]) for t in trials["upper"]))
    check("intro_no_real_deaths",trials["upper"][0]["actual_dead"]==[])
    check("train_and_three_six_survive",all(len(trials["upper"][i]["passed"])==6 for i in [4,5]))
    lu,shen,he,jiang,zhou,wen=trials["terminal"]["groups"][0]
    counts={n:sum(n in t["roster"] for t in trials["upper"]) for n in [lu,shen,he,jiang,zhou,wen]}
    check("core_repeat_limits",counts=={lu:6,shen:2,he:1,jiang:1,zhou:1,wen:1})
    check("six_middle_rosters",len(trials["middle"])==6 and all(len(t["roster"])==len(set(t["roster"]))==6 for t in trials["middle"]))
    middle_new=[n for t in trials["middle"] for n in t["roster"] if n!=lu]
    check("30_distinct_middle_supporting_people",len(middle_new)==len(set(middle_new))==30)
    groups=trials["terminal"]["groups"]; names=[n for g in groups for n in g]
    check("terminal_12x6_72_unique",len(groups)==12 and all(len(g)==6 for g in groups) and len(names)==len(set(names))==72)
    normal=trials["terminal"]["normal_survivors"]
    check("one_normal_survivor_protagonist_freed",len(set(normal))==1 and set(normal)<=set(names) and set(normal).isdisjoint(groups[0]) and lu not in normal)
    check("terminal_zero_brain_deaths_72_transfers",trials["terminal"]["actual_brain_deaths"]==0 and trials["terminal"]["phase3_transfer"]==72)
    r=trials["resource_checks"]
    check("silent_resource_balance",r["silent"]["initial"]+r["silent"]["collectable"]-r["silent"]["maintenance"]-r["silent"]["clock"]==r["silent"]["spare"]==12)
    check("terminal_resource_balance",r["terminal"]["fragments"]==r["terminal"]["fragments_per_seat"]*r["terminal"]["seats"]==36)
    check("birthday_within_168hours",r["birthday"]["max_cycles"]*r["birthday"]["hours_per_cycle"]==42<r["birthday"]["window_hours"])
    check("104_week_limit_all_six",all(0<timeline["terminal_week"]-w<=timeline["maximum_service_Vweeks"] for w in timeline["phase_entry_weeks"].values()))
    windows=timeline["middle_windows"]
    check("14_middle_windows_four_week_spacing",len(windows)==14 and all(windows[i+1]["week"]-windows[i]["week"]==4 for i in range(13)))
    check("real_virtual_alternation",all(w["kind"]==("real" if i%2==0 else "virtual") for i,w in enumerate(windows)))
    stored=load("state/population-calibration.json"); computed=calculate()
    check("population_result_reproducible",all(math.isclose(stored[k],computed[k],rel_tol=1e-10,abs_tol=1e-8) for k in computed))
    if ROOT.name == "overlay" and (ROOT.parent/"MANIFEST.json").exists():
        manifest=json.loads((ROOT.parent/"MANIFEST.json").read_text(encoding="utf-8"))
        safe=all(Path(x["path"]).parts[0] not in {"正文",".skill",".git"} for x in manifest["files"])
        safe=safe and not (ROOT/"正文").exists() and not (ROOT/".skill").exists()
        check("protected_paths_excluded_from_delivery",safe)
    elif (ROOT/".git").exists():
        # Writing-phase provenance guard: the skill library and the archived demo
        # must stay unchanged since the pre-writing baseline; new P-chapter files are deliverables.
        ok=True
        r1=subprocess.run(["git","-C",str(ROOT),"diff","--quiet","d1e21a0","HEAD","--",".skill"],capture_output=True)
        ok=ok and r1.returncode==0
        r2=subprocess.run(["git","-C",str(ROOT),"diff","--quiet","d1e21a0","HEAD","--","正文/终局场景-与蜂后对质-初稿.txt"],capture_output=True)
        ok=ok and r2.returncode==0
        check("protected_paths_unchanged_from_baseline",ok)
    else:
        check("protected_path_provenance_known",False,"Run in the delivery overlay or its target Git worktree.")
    bad_links=[]
    for f in ROOT.rglob("*.md"):
        txt=f.read_text(encoding="utf-8")
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)",txt):
            if target.startswith(("http:","https:","#","mailto:")): continue
            path=unquote(target.split("#",1)[0])
            if path and not (f.parent/path).exists(): bad_links.append(str(f.relative_to(ROOT))+": "+target)
    check("markdown_relative_links_resolve",not bad_links,"; ".join(bad_links))
    required=["meta/04-重大裁决与审阅顺序.md","meta/02-设定缺口追踪.md","state/handoff.md",
              "chapters/00-总大纲.md","chapters/06-开篇18章写作卡.md","chapters/08-规则反例与解法检查.md"]
    check("review_and_writing_entrypoints_present",all((ROOT/p).exists() for p in required))
    report={"scope":"finite structure, references, rosters, chronology and arithmetic; not semantic proof",
            "checks":checks,"passed":sum(x["passed"] for x in checks),"total":len(checks)}
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0 if report["passed"]==report["total"] else 1

if __name__=="__main__":
    raise SystemExit(main())
