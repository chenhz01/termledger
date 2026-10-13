#!/usr/bin/env python3
"""scaffold_gen.py — 突破件骨架工厂 (term-identity v0.2)
元突破件：从 blanks_spec.json 一键生成全部 57 件的动工级骨架+规格自测。
瘦身逻辑：52 件未实装件从「每次手写」变成「工厂批量生成，人工只填芯」。
状态纪律：骨架=动工级（接口+断言结构自检通过），实装后人工升 done——绝不把骨架冒充完毕。
"""
from __future__ import annotations
import json, sys
from pathlib import Path

ROOT = Path(__file__).parent
SPEC = ROOT / "blanks_spec.json"
OUT = ROOT / "pieces"

HEADER = '''#!/usr/bin/env python3
"""[{status}] {pid} · {blank_name} · {layer}层
{why}
接口契约：
{iface_doc}
断言规格（实装后必须全过）：
{assert_doc}
状态：动工级骨架——接口占位 NotImplementedError，实装后删除本行并跑自测。
"""
'''


def gen_skeleton(piece: dict, blank: dict) -> str:
    status = piece.get("status", "skeleton")
    if status == "done":
        return ""  # 已实装件不生成骨架
    iface_doc = "\n".join(f"  - {i}" for i in piece.get("iface", ["(见 blanks_spec.json)"]))
    assert_doc = "\n".join(f"  - {a}" for a in piece.get("assert", []))
    body = HEADER.format(status=status.upper(), pid=piece["id"], blank_name=blank["name"],
                         layer=blank["position"], why=blank["why"],
                         iface_doc=iface_doc, assert_doc=assert_doc)
    body += "from __future__ import annotations\nimport sys\n\n"
    for sig in piece.get("iface", []):
        # 从 "name(args) -> ret" 提取函数名生成占位
        fn = sig.split("(")[0].strip()
        body += f'def {fn}(*args, **kwargs):\n    raise NotImplementedError("[{piece["id"]}] 未实装——按头部断言规格填芯")\n\n\n'
    body += '''def _spec_selftest() -> int:
    """动工级自检：接口占位存在 + 规格非空（实装后替换为真断言）。"""
    import inspect
    fns = [n for n, o in inspect.getmembers(sys.modules[__name__], inspect.isfunction)
           if not n.startswith("_") and n != "main"]
    if not fns:
        print(f"[{__name__}] FAIL: 无接口函数")
        return 1
    print(f"[{__name__}] SKELETON-OK: 接口 {fns} 就位（动工级，实装后升 done）")
    return 0


if __name__ == "__main__":
    sys.exit(_spec_selftest())
'''
    return body


def main() -> int:
    spec = json.loads(SPEC.read_text(encoding="utf-8"))
    OUT.mkdir(exist_ok=True)
    made, skipped = [], []
    for blank in spec["blanks"]:
        for piece in blank["pieces"]:
            if piece.get("status") == "done":
                skipped.append(piece["id"])
                continue
            f = OUT / f"{piece['file']}.py"
            # 防覆盖保护：已实装文件（含 [DONE] 标记）永不覆盖——工厂幂等安全的根
            if f.exists() and "[DONE]" in f.read_text(encoding="utf-8"):
                skipped.append(piece["id"] + "(实装保护)")
                continue
            code = gen_skeleton(piece, blank)
            if code:
                f.write_text(code, encoding="utf-8")
                made.append(piece["id"])
    roadmap = {
        "total_spec": sum(len(b["pieces"]) for b in spec["blanks"]),
        "done_existing": skipped, "skeleton_generated": made,
        "next": "逐件填芯 → _spec_selftest 换真断言 → 升 done（每件一轮 写→验→报）"}
    (OUT / "_ROADMAP.json").write_text(json.dumps(roadmap, ensure_ascii=False, indent=2),
                                       encoding="utf-8")
    print(f"工厂产出：骨架 {len(made)} 件 / 已实装跳过 {len(skipped)} 件 / 规格总数 {roadmap['total_spec']}")
    print(f"明细：pieces/_ROADMAP.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
