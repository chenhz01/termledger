#!/usr/bin/env python3
"""[DONE] B15-1 · 查询服务（CLI 一体查询） · 下游层
term → 归一簇 + 证真 + 生命周期 三件套一体输出；未知术语不抛异常。
CLI 优先（瘦身=不建 HTTP 服务），结果落盘可复现。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "pieces"))

from term_ledger import normalize, cluster, fingerprint, DEFAULT_ALIAS  # noqa: E402


def query(term: str, verify_fn=None, lifecycle_rows: dict | None = None) -> dict:
    """单术语三件套。verify_fn 可注入（默认动态导入 term_verify；失败降级标注）。"""
    out: dict = {"term": term, "normalized": normalize(term, DEFAULT_ALIAS),
                 "fingerprint": fingerprint(normalize(term, DEFAULT_ALIAS))}
    demo = [term, term.replace("-", "_").replace("-", " "), term.upper()]
    out["identity_cluster"] = cluster(demo, DEFAULT_ALIAS)
    if verify_fn is None:
        try:
            from term_verify import verify as verify_fn  # type: ignore
        except Exception:
            verify_fn = None
    if verify_fn:
        try:
            card = verify_fn(term)
            out["verify"] = {"grade": card["grade"], "note": card["note"]}
        except Exception as e:
            out["verify"] = {"grade": "E?-降级", "note": f"证真失败: {type(e).__name__}"}
    else:
        out["verify"] = {"grade": "E?-降级", "note": "证真器不可用（离线降级，如实标注）"}
    r = (lifecycle_rows or {}).get(term)
    out["lifecycle"] = r if r else None
    return out


def query_many(terms: list[str]) -> dict:
    """批量：逐条隔离异常，汇总计数。"""
    rows, errs = [], 0
    for t in dict.fromkeys(terms):
        try:
            rows.append(query(t))
        except Exception:
            errs += 1
    return {"total": len(rows), "errors": errs, "rows": rows}


def _selftest() -> int:
    fails = []
    r = query("DeepSeek-V3.2", verify_fn=lambda t: {"grade": "E1-一手实存", "note": "mock"})
    if not {"term", "normalized", "fingerprint", "identity_cluster", "verify", "lifecycle"} <= set(r):
        fails.append(f"三件套键缺失: {list(r)}")
    r2 = query("zzz-none-xyz", verify_fn=lambda t: (_ for _ in ()).throw(RuntimeError("net")))
    if r2["verify"]["grade"] != "E?-降级":
        fails.append(f"降级失败: {r2['verify']}")
    if r2["lifecycle"] is not None:
        fails.append("无历史应null")
    m = query_many(["A", "A", "B"])
    if m["total"] != 2 or m["errors"] != 0:
        fails.append(f"批量异常: {m['total']}/{m['errors']}")
    if fails:
        print("term_api FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print("term_api selftest: 4/4 PASS")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(_selftest())
    terms = sys.argv[1:] or ["DeepSeek-V3.2"]
    report = query_many(terms)
    out = Path(__file__).parent / "api_query_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"\n[落盘: {out}]", file=sys.stderr)
