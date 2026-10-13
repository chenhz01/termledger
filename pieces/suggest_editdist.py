#!/usr/bin/env python3
"""[SKELETON] B05-1 · 消歧辅助（词典冷启动） · 上游/治理层
别名词典从零怎么来？编辑距离+共现自动建议，人只做确认
接口契约：
  - suggest(t1, t2) -> float
断言规格（实装后必须全过）：
  - 归一后比较
  - 阈值可配
  - 0-1区间
状态：动工级骨架——接口占位 NotImplementedError，实装后删除本行并跑自测。
"""
from __future__ import annotations
import sys

def suggest(*args, **kwargs):
    raise NotImplementedError("[B05-1] 未实装——按头部断言规格填芯")


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
