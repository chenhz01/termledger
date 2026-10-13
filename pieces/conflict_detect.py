#!/usr/bin/env python3
"""[SKELETON] B10-1 · 冲突仲裁 · 中游层
同一key多规范名冲突（大小写品牌之争）时谁赢需要规则
接口契约：
  - find(claims) -> list
断言规格（实装后必须全过）：
  - 同key不同value才报
  - 单claim安全
  - 含证据
状态：动工级骨架——接口占位 NotImplementedError，实装后删除本行并跑自测。
"""
from __future__ import annotations
import sys

def find(*args, **kwargs):
    raise NotImplementedError("[B10-1] 未实装——按头部断言规格填芯")


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
