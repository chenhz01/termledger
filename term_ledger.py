#!/usr/bin/env python3
"""term_ledger.py — AI 术语身份归一引擎 (term-identity v0.1)
空白A突破件：把「同一模型的不同写法」归并成一个规范身份簇。
设计要点：
  - 版本号是身份的一部分：GLM-5 与 GLM-6 必须不同簇（关键负例）
  - 别名词典驱动（中英映射/缩写），不做危险的自动缩写猜测
  - 指纹 = 归一化后的确定性哈希，跨日对账可复现
零第三方依赖，stdlib only。
"""
from __future__ import annotations
import hashlib, json, re, sys, unicodedata
from pathlib import Path

# ── 别名词典（可扩展：值=规范名；键=别名。加载 JSON 可覆盖/追加）──
DEFAULT_ALIAS = {
    "深度求索": "deepseek", "ds": "deepseek",           # 中文→英文
    "通义千问": "qwen", "千问": "qwen",
    "智谱": "zhipu", "清华智谱": "zhipu",
    "openai o系列": "o-series",
}

_WS = re.compile(r"[\s\-_\.]+")
# 版本尾段：可选前导分隔 + 可选单字母 v + 数字段（兼容 "深度求索3" 无分隔形态）
_VER_TAIL = re.compile(r"-?(?:v-)?\d+(?:-\d+)*$", re.IGNORECASE)
# camel 边界 + 字母↔数字边界都拆：Qwen3-Max 与 qwen 3 max 拆词后一致
_BOUND1 = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
_BOUND2 = re.compile(r"(?<=[A-Za-z])(?=\d)|(?<=\d)(?=[A-Za-z])")


def normalize(term: str, alias: dict[str, str] | None = None,
              keep_version: bool = True) -> str:
    """归一化：全半角→词边界拆词→小写→分隔符统一→别名→版本号策略。
    keep_version=True 保留尾部数字版本段（身份敏感），False 剥掉（家族级）。"""
    if not term or not term.strip():
        return ""
    t = unicodedata.normalize("NFKC", term).strip()
    t = _BOUND2.sub(" ", _BOUND1.sub(" ", t))
    t = _WS.sub("-", t.lower()).strip("-")
    if alias:
        # 别名按「去分隔符 key」查：整 key → 剥版本段 key，命中后拼回版本
        key = t.replace("-", "")
        if key in alias:
            t = _ws_dash(alias[key])
        else:
            m = _VER_TAIL.search(t)
            if m:
                root_key = t[:m.start()].replace("-", "")
                if root_key and root_key in alias:
                    t = _ws_dash(alias[root_key]) + m.group(0)
    if not keep_version:
        t = _VER_TAIL.sub("", t).strip("-")
    return t


def _key(s: str) -> str:
    """聚类键：任意写法 → 去分隔符小写。"""
    return re.sub(r"[\s\-_.]+", "", s.lower())


def _ws_dash(s: str) -> str:
    """词典值（如 deepseek）也过同一分隔符规范。"""
    return _WS.sub("-", unicodedata.normalize("NFKC", s).lower()).strip("-")


def fingerprint(norm: str) -> str:
    """确定性指纹（内部自动提 key，任意写法同指纹）：跨日跨进程可复现的对账锚点。"""
    k = _key(norm) if norm else ""
    return hashlib.sha1(k.encode("utf-8")).hexdigest()[:12] if k else ""


def cluster(terms: list[str], alias: dict[str, str] | None = None) -> dict[str, list[str]]:
    """按规范身份聚类（key=去分隔符指纹键，显示=首次出现的规范写法）。"""
    out: dict[str, tuple[str, list[str]]] = {}
    for raw in terms:
        n = normalize(raw, alias, keep_version=True)
        if not n:
            continue
        k = _key(n)
        if k in out:
            out[k][1].append(raw)
        else:
            out[k] = (n, [raw])
    ranked = sorted(out.items(), key=lambda kv: -len(kv[1][1]))
    return {disp: raws for _, (disp, raws) in ranked}


def families(terms: list[str], alias: dict[str, str] | None = None) -> dict[str, list[str]]:
    """家族级聚类：剥版本后取首段（粗粒度，语义=品牌词根）。"""
    out: dict[str, list[str]] = {}
    for raw in terms:
        n = normalize(raw, alias, keep_version=False)
        if n:
            fam = n.split("-")[0]
            out.setdefault(_key(fam), []).append(raw)
    return dict(sorted(out.items(), key=lambda kv: -len(kv[1])))


# ── 自测：断言即规格 ──────────────────────────────────────────
def _selftest() -> int:
    fails = []
    a = dict(DEFAULT_ALIAS)
    # 1. 分隔符/大小写归一 → 同簇（显示名取首次规范写法）
    g = cluster(["DeepSeek-V3.2", "deepseek_v3.2", "DEEPSEEK V3.2", "deepseek.v3.2"], a)
    if len(g) != 1 or len(list(g.values())[0]) != 4:
        fails.append(f"分隔符归一失败: {g}")
    # 2. 版本号区分身份（关键负例：GLM-5 ≠ GLM-6）
    g = cluster(["GLM-5", "GLM-6", "glm 5"], a)
    if set(g.keys()) != {"glm-5", "glm-6"}:
        fails.append(f"版本号身份失败: {g}")
    # 3. camelCase 拆词
    if normalize("CodeBuddyCLI") != "code-buddy-cli":
        fails.append(f"camelCase失败: {normalize('CodeBuddyCLI')}")
    # 4. 中文别名映射（词典值过同一规范，含版本拼接）
    if normalize("深度求索-V3.2", a) != normalize("deepseek-v3.2"):
        fails.append(f"中文别名失败: {normalize('深度求索-V3.2', a)}")
    # 4b. 中文别名家族级：剥版本后命中
    if normalize("深度求索3", a, keep_version=False) != "deepseek":
        fails.append(f"中文别名家族失败: {normalize('深度求索3', a, keep_version=False)}")
    # 5. 家族级：剥版本后归并
    f = families(["Qwen3-Max", "qwen 3 max", "Qwen2.5", "通义千问3"], a)
    if set(f.keys()) != {"qwen"} or len(f["qwen"]) != 4:
        fails.append(f"家族归并失败: {f}")
    # 6. 指纹确定性
    if fingerprint(normalize("DeepSeek-V3.2")) != fingerprint(normalize("deepseek_v3.2")):
        fails.append("指纹不确定")
    # 7. 全半角
    if normalize("ＧＬＭ－５") != "glm-5":
        fails.append(f"全半角失败: {normalize('ＧＬＭ－５')}")
    # 8. 空值边界
    if normalize("   ") != "" or fingerprint("") != "":
        fails.append("空值边界失败")
    # 9. Qwen3-Max 与 qwen 3 max 同簇（数字边界拆词一致性）
    g = cluster(["Qwen3-Max", "qwen 3 max"], a)
    if len(g) != 1:
        fails.append(f"数字边界一致性失败: {g}")
    # 10. 指纹用 key：不同分隔写法同指纹
    if fingerprint("glm-5") != fingerprint("glm 5"):
        fails.append("指纹key不一致")
    if fails:
        print("SELFTEST FAIL:")
        [print("  -", x) for x in fails]
        return 1
    print("term_ledger selftest: 10/10 PASS")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--selftest":
        sys.exit(_selftest())
    # CLI：stdin 喂术语（每行一个），stdout 出簇对账 JSON
    raws = [l.strip() for l in sys.stdin if l.strip()]
    print(json.dumps({"identity_clusters": cluster(raws, DEFAULT_ALIAS),
                      "families": families(raws, DEFAULT_ALIAS),
                      "total_raw": len(raws),
                      "total_identity": len(cluster(raws, DEFAULT_ALIAS))},
                     ensure_ascii=False, indent=2))
