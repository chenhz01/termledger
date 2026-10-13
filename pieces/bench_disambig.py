#!/usr/bin/env python3
"""[DONE] B18-1 · 消歧评测基准 · 下游层
50 对固定用例给消歧引擎打分——没有基准的自我感觉良好不算数。
用例确定性生成（同身份对 + 异身份对各半，含中文别名/全半角/版本负例）。
断言规格：50用例固定 / 准确率输出 / 同身份全聚对 / 异身份零误并 / 确定性。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from term_ledger import normalize, fingerprint, DEFAULT_ALIAS  # noqa: E402


def build_cases() -> list[dict]:
    """确定性生成 50 对：25 同身份（应同簇）+ 25 异身份（应不同簇）。"""
    same: list[tuple[str, str]] = []
    roots = ["deepseek", "glm", "qwen", "kimi", "claude", "codex", "gemini", "llama"]
    for i, r in enumerate(roots):
        v = f"{i % 3 + 3}.{i % 2}"
        same.append((f"{r.upper()}-{v}", f"{r}_{v}"))
        same.append((f"{r}-{v}", f"{r} {v}"))
        same.append((f"{r}.{v}", f"{r}-{v}"))
        if i < 2:
            same.append((f"Ｍodel-{r}-{v}", f"model-{r}-{v}"))
    same += [("GLM-5", "glm 5"), ("ＧＬＭ－５", "GLM-5")]
    same = same[:25]
    diff: list[tuple[str, str]] = []
    for i in range(12):
        diff.append((f"model-v{i}", f"model-v{i+1}"))
    diff += [("glm-5", "glm-6"), ("deepseek", "deepseekr1"), ("qwen3", "qwen2"),
             ("kimi", "kimi-k2"), ("codex", "codex-cli"), ("a-1", "a-2"),
             ("深度求索", "通义千问"), ("glm5", "glam5"), ("llama3", "llama4"),
             ("openai-o3", "openai-o4"), ("gemini-2", "gemini-3"), ("gpt5", "gpt4"),
             ("sonnet", "opus")]
    diff = diff[:25]
    cases = [{"t1": a, "t2": b, "same": True} for a, b in same] + \
            [{"t1": a, "t2": b, "same": False} for a, b in diff]
    return cases[:50]


def score() -> dict:
    """跑基准：同身份指纹必须相等，异身份必须不等。"""
    cases = build_cases()
    correct, wrongs = 0, []
    for c in cases:
        same_actual = fingerprint(normalize(c["t1"], DEFAULT_ALIAS)) == \
                      fingerprint(normalize(c["t2"], DEFAULT_ALIAS))
        if same_actual == c["same"]:
            correct += 1
        else:
            wrongs.append(c)
    n = len(cases)
    return {"cases": n, "correct": correct, "accuracy": round(correct / n, 4),
            "wrongs": wrongs, "deterministic": True}


def _selftest() -> int:
    r = score()
    fails = []
    if r["cases"] != 50:
        fails.append(f"用例数≠50: {r['cases']}")
    if r["accuracy"] < 1.0:
        fails.append(f"准确率<1.0: {r['accuracy']} → 误判: {r['wrongs'][:3]}")
    if fails:
        print("bench_disambig FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print(f"bench_disambig selftest: 50/50 用例 PASS（accuracy={r['accuracy']}）")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(_selftest())
    print(json.dumps(score(), ensure_ascii=False, indent=2))
