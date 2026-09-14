#!/usr/bin/env python3
"""Author-only fictional population calibration; not a real demographic forecast."""
import json
import math
from pathlib import Path

def calculate(entry_vyear=21186.0, exit_hazard=0.025, elapsed_ryears=16.0):
    survival = 2.0/3.0
    trial_count = 9
    spacing_vyears = 4.0/52.0
    progression = survival ** trial_count
    phase1_stock = entry_vyear * spacing_vyears * sum(survival**k for k in range(trial_count))
    entry2_v = entry_vyear * progression
    real_fatality, virtual_transition = 0.02, 1.0/3.0
    cycle_survival = (1-real_fatality)*(1-virtual_transition)
    real_exit_share = real_fatality/(1-cycle_survival)
    expected_checks = (2-real_fatality)/(1-cycle_survival)
    time2_v = ((expected_checks-1)*4+0.5)/52
    entry3_r = entry2_v*(1-real_exit_share)/2
    risk = sum(w*p for w,p in zip([.50,.25,.15,.07,.03],[.002,.006,.018,.045,.10]))
    hazard = -13*math.log1p(-risk)
    total = entry3_r * (-math.expm1(-hazard*elapsed_ryears))/hazard
    front = entry3_r * (-math.expm1(-(hazard+exit_hazard)*elapsed_ryears))/(hazard+exit_hazard)
    release = 12000 + 800 + entry_vyear*(1-progression) + entry2_v*real_exit_share + 2*hazard*total
    return dict(
        C=entry_vyear, phase1_stock=phase1_stock, phase2_stock=entry2_v*time2_v,
        phase2_entry_per_Vyear=entry2_v, real_death_share_phase2=real_exit_share,
        phase3_entry_per_Ryear=entry3_r, phase3_mean_task_death=risk,
        phase3_hazard_per_Ryear=hazard, phase3_continuous_mean_years=1/hazard,
        phase3_total_at_R20=total, phase3_front_at_R20=front,
        phase3_outside_at_R20=total-front, birth_release_per_Vyear=release)

def test():
    x=calculate()
    assert 4750 < x["phase1_stock"] < 4780
    assert 1390 < x["phase3_front_at_R20"] < 1420
    assert 170 < x["phase3_outside_at_R20"] < 195
    assert abs(x["phase3_total_at_R20"]-x["phase3_front_at_R20"]-x["phase3_outside_at_R20"]) < 1e-8
    assert 0 < x["real_death_share_phase2"] < 1
    assert abs(x["phase3_mean_task_death"]-.01135) < 1e-12

if __name__ == "__main__":
    test()
    print(json.dumps(calculate(), indent=2, ensure_ascii=False))
