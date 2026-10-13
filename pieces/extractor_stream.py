#!/usr/bin/env python3
"""[SKELETON] B02-1 · 术语抽取器 · 上游层
radar 用正则集，缺 camel/版本号/中文混合的流式抽取
接口契约：
  - extract(text) -> list[str]
断言规格（实装后必须全过）：
  - camelCase保留
  - 版本号附着
  - 停用词过滤
状态：动工级骨架——接口占位 NotImplementedError，实装后删除本行并跑自测。
"""
from __future__ import annotations
import sys

def extract(*args, **kwargs):
    raise NotImplementedError("[B02-1] 未实装——按头部断言规格填芯")


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
