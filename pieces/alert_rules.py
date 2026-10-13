#!/usr/bin/env python3
"""[DONE] B13-1 · 告警规则引擎 · 下游层
把证真报告 × 生命周期报告 → 分级告警（不再一锅端日报）。
分级：E0无源=HIGH(幻觉风险) / 假爆发=MED / 衰退=LOW / 真爆发+E1=OPP(机会)。
断言规格：E0→HIGH / 假爆发→MED / 分级阈值可配 / 去重 / 纯文本安全。
"""
from __future__ import annotations
import sys

SEVERITY_ORDER = {"HIGH": 0, "MED": 1, "LOW": 2, "OPP": 3}


def evaluate(verify_report: dict, lifecycle_report: dict,
             thresholds: dict | None = None) -> list[dict]:
    """两份报告 → 告警清单。thresholds 可覆盖默认分级映射。"""
    th = {"e0": "HIGH", "fake": "MED", "fade": "LOW", "surge": "OPP",
          "min_gh_repos": 1, "max_alerts": 50, **(thresholds or {})}
    alerts: list[dict] = []
    seen: set = set()

    def add(sev, term, msg):
        if (sev, term) in seen or len(alerts) >= th["max_alerts"]:
            return
        seen.add((sev, term))
        alerts.append({"severity": sev, "term": term, "msg": msg})

    for c in verify_report.get("cards", []):
        if c.get("grade") == "E0-无源" and len(c.get("gh_repos", [])) < th["min_gh_repos"]:
            add(th["e0"], c["term"], "无源术语：疑似幻觉词/营销词，禁入对外文本")
    rows = {r["term"]: r for r in lifecycle_report.get("rows", [])}
    for term, r in rows.items():
        if r.get("fake_surge"):
            add(th["fake"], term, "假爆发（单日脉冲后归零）：勿当真实趋势传播")
        elif r.get("fade_day"):
            add(th["fade"], term, f"衰退确认（{r['fade_day']}日起 <峰值20%）：降低关注度")
        elif r.get("surge_day"):
            add(th["surge"], term, f"真爆发（{r['surge_day']}日触发）：关注窗口打开")
    return sorted(alerts, key=lambda a: (SEVERITY_ORDER[a["severity"]], a["term"]))


def digest(alerts: list[dict]) -> str:
    """纯文本摘要（去重 + 按级排序 + 截断保护）。"""
    seen, uniq = set(), []
    for a in alerts:
        k = (a["severity"], a["term"])
        if k not in seen:
            seen.add(k)
            uniq.append(a)
    uniq.sort(key=lambda a: (SEVERITY_ORDER[a["severity"]], a["term"]))
    lines = []
    for a in uniq[:30]:
        lines.append(f"[{a['severity']}] {a['term']}: {a['msg']}")
    if len(uniq) > 30:
        lines.append(f"...其余 {len(uniq)-30} 条省略")
    return "\n".join(lines) if lines else "(无告警)"


def _selftest() -> int:
    fails = []
    vr = {"cards": [
        {"term": "ghost-word", "grade": "E0-无源", "gh_repos": []},
        {"term": "real-one", "grade": "E1-一手实存", "gh_repos": [{"full_name": "x"}]}]}
    lr = {"rows": [
        {"term": "vaporsdk", "fake_surge": True, "surge_day": None, "fade_day": None},
        {"term": "flashtrade-v2", "fake_surge": False, "surge_day": 9, "fade_day": 14},
        {"term": "steady-hit", "fake_surge": False, "surge_day": 11, "fade_day": None}]}
    alerts = evaluate(vr, lr)
    sev = {a["term"]: a["severity"] for a in alerts}
    if sev.get("ghost-word") != "HIGH":
        fails.append(f"E0应为HIGH: {sev}")
    if sev.get("vaporsdk") != "MED":
        fails.append(f"假爆发应为MED: {sev}")
    if sev.get("flashtrade-v2") != "LOW":
        fails.append(f"衰退应为LOW: {sev}")
    if sev.get("steady-hit") != "OPP":
        fails.append(f"真爆发应为OPP: {sev}")
    alerts2 = evaluate(vr, lr, {"e0": "LOW"})
    if {a["term"]: a["severity"] for a in alerts2}["ghost-word"] != "LOW":
        fails.append("阈值覆盖失败")
    d = digest(alerts)
    if "ghost-word" not in d or len(digest(alerts * 2).splitlines()) != len(d.splitlines()):
        fails.append("digest去重/截断失败")
    if fails:
        print("alert_rules FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print("alert_rules selftest: 6/6 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(_selftest())
