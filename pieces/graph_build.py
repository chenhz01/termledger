#!/usr/bin/env python3
"""[SKELETON] B09-1 · 家族图谱 · 中游层
家族(family)→repo/org/作者关系图，版本谱系可视化
接口契约：
  - build(families, repos) -> dict
断言规格（实装后必须全过）：
  - 节点唯一
  - 边去重
  - 孤立点保留
状态：动工级骨架——接口占位 NotImplementedError，实装后删除本行并跑自测。
"""
from __future__ import annotations
import sys

def build(*args, **kwargs):
    raise NotImplementedError("[B09-1] 未实装——按头部断言规格填芯")


def _spec_selftest() -> int:
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
