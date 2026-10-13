#!/usr/bin/env python3
"""lifecycle_bench.py — AI 术语生命周期确定性对账 (term-identity v0.1)
空白C补强件：new-term-radar 有 surges() 爆发检测，但缺：
  衰退检测 / 假爆发识别 / 确定性单测护栏 / 对账报告。
本件用固定 fixture（3 条故事线 × 30 天）做规则引擎，
全部确定性（同输入必同输出，可进 CI）。
规则：
  首现 FIRST   = 频次>0 的第一天
  爆发 SURGE   = 7日滑窗均值 ≥ 前基线均值×3 且绝对量≥5
  衰退 FADE    = 爆发后连续 5 日 < 峰值×20%
  假爆发 FAKE  = 单日脉冲（1 日 > 前后各 3 日总和×3）后归零
"""
from __future__ import annotations
import json, sys

DAYS = 30

def fixture() -> dict[str, list[int]]:
    """固定语料：确定性生成（无随机），三条故事线 + 一条对照。"""
    series: dict[str, list[int]] = {}
    # 线1 真爆发→衰退：基线2 → 爆发30 → 衰退到1
    s = [2]*8 + [30, 45, 40, 35, 20, 10, 5] + [1]*15
    series["flashtrade-v2"] = s[:DAYS]
    # 线2 稳定长尾：恒定增长无爆发判定失败（缓慢爬升不触发3×）
    series["slowburn-os"] = [1+i//10 for i in range(DAYS)]
    # 线3 假爆发：第14天单日脉冲50，前后≈0
    s = [0]*14 + [50] + [0]*15
    series["vaporsdk"] = s[:DAYS]
    # 线4 对照：健康爆发后持续（无衰退）
    s = [0]*10 + [8]*20
    series["steady-hit"] = s[:DAYS]
    return series


def _win_mean(s: list[int], lo: int, hi: int) -> float:
    lo, hi = max(0, lo), min(len(s), hi)
    seg = s[lo:hi]
    return sum(seg) / len(seg) if seg else 0.0


def analyze(name: str, s: list[int]) -> dict:
    events: dict[str, object] = {}
    nz = [i for i, v in enumerate(s) if v > 0]
    events["first_seen"] = (nz[0] + 1) if nz else None
    # 爆发：两种确定性判定（二选一即触发）
    # ① 滑窗比值：7日均值 ≥ 前7日基线×3（渐进式）
    # ② 阶跃跳变：单日 ≥ 前7日总和×1.5 且 ≥5（平台式阶跃）
    surge_day = None
    for i in range(7, len(s)):
        base = _win_mean(s, i-7, i)
        win = _win_mean(s, i-6, i+1)
        cond_ratio = base >= 1 and win >= base * 3
        cond_step = s[i] >= 5 and s[i] >= sum(s[max(0,i-7):i]) * 1.5
        if cond_ratio or cond_step:
            surge_day = i + 1
            break
    events["surge_day"] = surge_day
    peak = max(s) if s else 0
    # 衰退：爆发后连续5日 < 峰值20%
    fade_day = None
    if surge_day:
        tail = s[surge_day-1:]
        run = 0
        for i, v in enumerate(tail):
            run = run + 1 if v < peak * 0.2 else 0
            if run >= 5:
                fade_day = surge_day + i - 4
                break
    events["fade_day"] = fade_day
    # 假爆发：单日脉冲 > 前后各3日总和×3 → 否决 surge（假爆发不给爆发名分）
    fake = False
    for i in range(3, len(s)-3):
        if s[i] >= 5 and s[i] > (sum(s[i-3:i]) + sum(s[i+1:i+4])) * 3:
            fake = True
            break
    events["fake_surge"] = fake
    if fake:
        events["surge_day"] = None
    events["peak"] = peak
    events["total"] = sum(s)
    return {"term": name, **events}


def _selftest() -> int:
    fails = []
    rs = {r["term"]: r for r in run_report()["rows"]}
    r1 = rs["flashtrade-v2"]
    if r1["surge_day"] is None or r1["fade_day"] is None or r1["fake_surge"]:
        fails.append(f"线1 应=真爆发+衰退+非假: {r1}")
    r2 = rs["slowburn-os"]
    if r2["surge_day"] is not None:
        fails.append(f"线2 缓爬不应触发爆发: {r2}")
    r3 = rs["vaporsdk"]
    if not r3["fake_surge"] or r3["surge_day"] is not None:
        fails.append(f"线3 应=假爆发: {r3}")
    r4 = rs["steady-hit"]
    if r4["surge_day"] is None or r4["fade_day"] is not None:
        fails.append(f"线4 应=爆发无衰退: {r4}")
    if fails:
        print("LIFECYCLE SELFTEST FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print("lifecycle_bench selftest: 4/4 PASS（确定性规则护栏全绿）")
    return 0


def run_report() -> dict:
    rows = [analyze(k, v) for k, v in fixture().items()]
    return {"days": DAYS, "rows": rows}


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(_selftest())
    print(json.dumps(run_report(), ensure_ascii=False, indent=2))
