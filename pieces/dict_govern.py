#!/usr/bin/env python3
"""[DONE] B03-1 · 别名词典治理 · 上游/治理层
外部化 term_ledger 的内置词典：加载/合并/冲突与环检测。
断言规格：同value多key合法 / key=value自指报错 / 环检测 / 合并确定性。
"""
from __future__ import annotations
import json, sys
from pathlib import Path


def load(path: str | Path) -> dict[str, str]:
    """加载词典 JSON，格式非法即抛 ValueError（fail-loud）。"""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    validate(d, strict=True)
    return {k: v for k, v in d.items()}


def validate(d: dict, strict: bool = False) -> list[str]:
    """词典校验：返回问题清单；strict=True 有问题即抛。"""
    problems = []
    if not isinstance(d, dict):
        problems.append("根必须是对象")
    for k, v in (d or {}).items():
        if not str(k).strip() or not str(v).strip():
            problems.append(f"空键/空值: {k!r}")
        if str(k).lower() == str(v).lower():
            problems.append(f"自指映射: {k}→{v}")
    if strict and problems:
        raise ValueError("; ".join(problems))
    return problems


def merge(a: dict, b: dict) -> dict:
    """合并：b 优先（新词典赢），键排序确定性。"""
    return dict(sorted({**a, **b}.items()))


def detect_conflicts(*dicts: dict) -> list[dict]:
    """冲突检测：①同 key 不同 value（跨词典打架）②value→key 环。"""
    conflicts = []
    seen: dict[str, set] = {}
    for d in dicts:
        for k, v in d.items():
            seen.setdefault(k, set()).add(str(v))
    for k, vs in seen.items():
        if len(vs) > 1:
            conflicts.append({"type": "key-fight", "key": k, "values": sorted(vs)})
    merged = {k: str(v).lower() for d in dicts for k, v in d.items()}
    for start in merged:
        cur, hops = start.lower(), 0
        while cur in merged and hops <= len(merged):
            cur = merged[cur]
            hops += 1
            if cur == start.lower():
                conflicts.append({"type": "cycle", "key": start})
                break
    return conflicts


def _selftest() -> int:
    fails = []
    good = {"深度求索": "deepseek", "ds": "deepseek"}
    if validate(good):
        fails.append(f"合法词典误报: {validate(good)}")
    if not any("自指" in p for p in validate({"glm": "GLM"})):
        fails.append("自指漏检")
    cyc = detect_conflicts({"aa": "bb"}, {"bb": "aa"})
    if not any(c["type"] == "cycle" for c in cyc):
        fails.append(f"环漏检: {cyc}")
    fight = detect_conflicts({"x": "1"}, {"x": "2"})
    if not any(c["type"] == "key-fight" for c in fight):
        fails.append(f"打架漏检: {fight}")
    m = merge({"a": "1", "b": "1"}, {"b": "2"})
    if m != {"a": "1", "b": "2"} or list(m) != ["a", "b"]:
        fails.append(f"合并错误: {m}")
    if validate({"ds": "deepseek", "深度求索": "deepseek"}):
        fails.append("同value多key误报")
    try:
        validate({"bad": ""}, strict=True)
        fails.append("strict未抛")
    except ValueError:
        pass
    if fails:
        print("dict_govern FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print("dict_govern selftest: 7/7 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(_selftest())
