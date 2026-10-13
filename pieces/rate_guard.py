#!/usr/bin/env python3
"""[SKELETON] B16-2 · 缓存与限速 · 下游/基建层
gh/HF 调用成本高：缓存命中=省积分，限速=防封
接口契约：
  - allow() -> bool
断言规格（实装后必须全过）：
  - 滑动窗口
  - 超限拒绝不抛异常
  - 剩余额度查询
状态：动工级骨架——接口占位 NotImplementedError，实装后删除本行并跑自测。
"""
from __future__ import annotations
import sys

def allow(*args, **kwargs):
    raise NotImplementedError("[B16-2] 未实装——按头部断言规格填芯")


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
