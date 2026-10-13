#!/usr/bin/env python3
"""term_verify.py — AI 术语证真器 (term-identity v0.1)
空白B突破件：新术语到底是「真东西」还是「营销词/幻觉词」？
三级证据分级 + 四级来源标注（F11 对齐）：
  E1 一手实存：GitHub repo 实搜命中 / HuggingFace 实搜命中
  E2 二手引用：无实存但别名/家族词有实存（可能是版本写法差异）
  E0 无源：两源皆空 → ⚠️ 疑似幻觉词/纯营销词，禁入对外文本
输出 JSON 证真报告卡，一条命令复现。
"""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from term_ledger import normalize, DEFAULT_ALIAS  # 复用归一层，不做两套标准

GH = "gh"  # 依赖 gh CLI（已有环境）；HF 走公开 API


def gh_search(term: str, limit: int = 3) -> list[dict]:
    """GitHub 实搜：星数≥50 的仓才算实存信号（过滤同名噪音）。"""
    q = f"{term} in:name,description stars:>50"
    try:
        r = subprocess.run(
            [GH, "api", f"search/repositories?q={q.replace(' ', '+')}&sort=stars&per_page={limit}",
             "--jq", ".items[] | {full_name, stars: .stargazers_count, lang: .language, desc: (.description // \"\" | .[0:80])}"],
            capture_output=True, text=True, timeout=30)
        if r.returncode != 0 or not r.stdout.strip():
            return []
        return [json.loads(l) for l in r.stdout.strip().splitlines() if l.strip().startswith("{")]
    except Exception:
        return []


def hf_search(term: str, limit: int = 3) -> list[dict]:
    """HuggingFace 实搜：模型/数据集实存信号。"""
    try:
        r = subprocess.run(
            [GH, "api", f"https://huggingface.co/api/models?search={term}&limit={limit}",
             "--jq", ".[] | {model: .modelId, downloads: .downloads}",
             "-H", "Accept: application/json"],
            capture_output=True, text=True, timeout=30)
        if r.returncode != 0 or not r.stdout.strip():
            return []
        return [json.loads(l) for l in r.stdout.strip().splitlines() if l.strip().startswith("{")]
    except Exception:
        return []


def verify(term: str) -> dict:
    """单术语证真：返回证据卡。"""
    norm = normalize(term, DEFAULT_ALIAS)
    repos = gh_search(norm)
    models = hf_search(norm)
    if repos:
        grade, note = "E1-一手实存", f"GitHub 实搜命中 {len(repos)} 仓"
    elif models:
        grade, note = "E1-一手实存", f"HF 实搜命中 {len(models)} 模型"
    else:
        fam = normalize(term, DEFAULT_ALIAS, keep_version=False)
        repos_f = gh_search(fam) if fam != norm else []
        grade, note = ("E2-二手引用", f"家族词「{fam}」有实存，本版本写法待观察") if repos_f \
            else ("E0-无源", "⚠️ 两源皆空：疑似幻觉词/纯营销词，禁入对外文本（F11）")
    return {"term": term, "normalized": norm, "grade": grade, "note": note,
            "gh_repos": repos[:3], "hf_models": models[:3]}


def main() -> None:
    terms = sys.argv[1:] or [l.strip() for l in sys.stdin if l.strip()]
    cards = [verify(t) for t in terms]
    counts = {}
    for c in cards:
        counts[c["grade"]] = counts.get(c["grade"], 0) + 1
    report = {"verified_at": "runtime", "total": len(cards), "grade_summary": counts,
              "cards": cards}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    # 证真报告卡落盘（对账可复现）
    out = Path(__file__).parent / "verify_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n[报告卡已落盘: {out}]", file=sys.stderr)


if __name__ == "__main__":
    main()
