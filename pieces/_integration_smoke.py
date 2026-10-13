#!/usr/bin/env python3
"""[组合冒烟] 单仓→组合全链路：词典治理→归一→证真(离线注入)→告警→基准。
通过标准：五段串联零断裂 + 端到端断言全过。离线确定性（证真 mock 注入）。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pieces"))

from dict_govern import merge, validate, detect_conflicts
from term_ledger import normalize, fingerprint, DEFAULT_ALIAS
from term_api import query
from alert_rules import evaluate, digest
import bench_disambig


def main() -> int:
    fails = []
    # 1. 词典层：外部词典与内置合并 + 冲突检出
    external = {"k2": "kimi", "moonshot": "kimi"}
    d = merge(DEFAULT_ALIAS, external)
    if conflicts := [c for c in detect_conflicts(DEFAULT_ALIAS, external) if c["type"] == "cycle"]:
        fails.append(f"词典层环误报: {conflicts}")
    if normalize("K2", d) != normalize("kimi"):
        fails.append(f"词典→归一断裂: {normalize('K2', d)}")
    # 2. 归一层：指纹一致
    if fingerprint(normalize("DeepSeek-V3.2", d)) != fingerprint(normalize("deepseek_v3.2", d)):
        fails.append("归一层指纹断裂")
    # 3. 证真层（离线 mock 注入）：E0 分级进告警
    mock_verify = lambda t: {"grade": "E0-无源", "note": "离线注入", "gh_repos": [], "hf_models": []} \
        if "ghost" in t else {"grade": "E1-一手实存", "note": "离线注入", "gh_repos": [{"full_name": "a/b"}], "hf_models": []}
    vr = {"cards": [dict(term=t, **mock_verify(t)) for t in ["ghost-term-x", "DeepSeek-V3.2"]]}
    # 4. 告警层：E0→HIGH
    lr = {"rows": [{"term": "ghost-term-x", "fake_surge": True, "surge_day": None, "fade_day": None},
                   {"term": "DeepSeek-V3.2", "fake_surge": False, "surge_day": 9, "fade_day": None}]}
    alerts = evaluate(vr, lr)
    pairs = {(a["term"], a["severity"]) for a in alerts}
    if ("ghost-term-x", "HIGH") not in pairs or ("DeepSeek-V3.2", "OPP") not in pairs:
        fails.append(f"告警层断裂: {pairs}")
    d_text = digest(alerts)
    if "ghost-term-x" not in d_text:
        fails.append("digest断裂")
    # 5. 基准层：accuracy=1.0
    if bench_disambig.score()["accuracy"] < 1.0:
        fails.append("基准层断裂")
    # 6. 一体查询：query 走通（verify 注入 mock；lifecycle 传 term→row 映射）
    rows_map = {r["term"]: r for r in lr["rows"]}
    q = query("DeepSeek-V3.2", verify_fn=mock_verify, lifecycle_rows=rows_map)
    if q["verify"]["grade"] != "E1-一手实存" or not q["lifecycle"]:
        fails.append(f"一体查询断裂: {q.get('verify')}")
    if fails:
        print("INTEGRATION SMOKE FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print("INTEGRATION SMOKE: 6/6 断言 PASS（词典→归一→证真→告警→基准 全链路通）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
