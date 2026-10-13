#!/usr/bin/env python3
"""[DONE] B16-1 · 缓存存储（TTL + 磁盘持久） · 下游/基建层
瘦身基建：gh/HF 调用结果缓存命中=直接省积分。TTL 过期、磁盘持久、跨实例共享。
断言规格：TTL过期 / 磁盘持久 / 缓存未命中返回None / put幂等覆盖 / stale降级标注。
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path


class Cache:
    def __init__(self, dir: str | Path, ttl: int = 86400):
        self.dir = Path(dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

    def _path(self, key: str):
        safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in key)[:80]
        return self.dir / f"{safe}.json"

    def put(self, key: str, value) -> None:
        """写入（幂等覆盖，带写入时间戳）。"""
        self._path(key).write_text(json.dumps(
            {"t": time.time(), "v": value}, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str, now: float | None = None):
        """命中返回值；过期/未命中返回 None。now 可注入（测试确定性）。"""
        p = self._path(key)
        if not p.exists():
            return None
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return None
        ts = rec.get("t", 0)
        age = (now if now is not None else time.time()) - ts
        if age > self.ttl:
            return None
        return rec.get("v")

    def get_stale(self, key: str, now: float | None = None):
        """过期也返回（标注 stale）——离线降级用，绝不静默造假：调用方必须看 stale 标记。"""
        p = self._path(key)
        if not p.exists():
            return None, False
        rec = json.loads(p.read_text(encoding="utf-8"))
        fresh = ((now if now is not None else time.time()) - rec.get("t", 0)) <= self.ttl
        return rec.get("v"), fresh


def _selftest() -> int:
    import tempfile
    fails = []
    with tempfile.TemporaryDirectory() as td:
        c = Cache(td, ttl=60)
        if c.get("nope") is not None:
            fails.append("未命中应None")
        c.put("k1", {"a": 1})
        c.put("k1", {"a": 2})
        if c.get("k1") != {"a": 2}:
            fails.append("幂等覆盖失败")
        c2 = Cache(td, ttl=60)
        if c2.get("k1") != {"a": 2}:
            fails.append("持久化失败")
        if Cache(td, ttl=60).get("k1", now=time.time() + 61) is not None:
            fails.append("TTL未过期")
        v, fresh = c.get_stale("k1")
        if v != {"a": 2} or not fresh:
            fails.append(f"stale新鲜失败: {v}, fresh={fresh}")
        v2, fresh2 = c.get_stale("k1", now=time.time() + 61)
        if v2 != {"a": 2} or fresh2:
            fails.append(f"stale过期失败: {v2}, fresh={fresh2}")
        c.put("term/deep seek v3.2?", 1)
        if c.get("term/deep seek v3.2?") != 1:
            fails.append("特殊key失败")
    if fails:
        print("cache_store FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print("cache_store selftest: 6/6 PASS")
    return 0


if __name__ == "__main__":
    sys.exit(_selftest())
