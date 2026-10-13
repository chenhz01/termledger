# TermLedger — one term, one identity. With a receipt.

> `DeepSeek-V3.2`, `deepseek_v3.2`, `深度求索V3` — three spellings, one model. Most "AI term radars" count them as **three different trends**. TermLedger resolves them into **one identity**, verifies the term actually *exists*, and tells real surges from single-day fakes. Every number below reproduces with one command.

[![status](https://img.shields.io/badge/spec-19_blanks_×_3_layers-5eead4)](blanks_spec.json) [![engines](https://img.shields.io/badge/engines-8_runnable_·_selftested-34d399)](#quickstart) [![deps](https://img.shields.io/badge/deps-zero_stdlib_only-7dd3fc)](#) [![license](https://img.shields.io/badge/license-MIT-8b94ab)](LICENSE)

**中文**：AI 新术语雷达很多，术语的「身份对账层」一个都没有。本项目做三件事：①把同一模型的 N 种写法归并成一个规范身份（版本号即身份：GLM-5 ≠ GLM-6）；②对新术语做实存证真——**无源的词当场标记为疑似幻觉词/营销词，禁止流入你的对外文本**；③给术语装上确定性生命周期对账（真爆发 / 假爆发 / 衰退，同一输入必同输出）。

## Quickstart

```bash
python term_ledger.py --selftest        # 归一引擎：10/10 断言
python lifecycle_bench.py --selftest    # 生命周期：4/4 确定性护栏
python pieces/bench_disambig.py --selftest   # 消歧基准：50/50（accuracy=1.0）
python pieces/dict_govern.py --selftest # 词典治理：7/7（环检测/冲突/自指）
python pieces/alert_rules.py --selftest # 四级告警：6/6
python pieces/cache_store.py --selftest # 缓存基建：6/6
python pieces/term_api.py --selftest    # 一体查询：4/4
python pieces/_integration_smoke.py     # 全链路组合冒烟：6/6
python term_verify.py "DeepSeek-V3.2" "some-hallucinated-name"   # 真数据证真
```

## Why it exists

AI 术语生态的荒诞现状：抓取层繁荣（radar/trending/list 满天飞），**身份层空白**——

| 荒诞 | 后果 |
|---|---|
| 同一模型 4 种写法被当成 4 个趋势 | 热度被稀释，判断被污染 |
| 营销词/幻觉词与真东西同版面 | 你引用了一个不存在的模型 |
| 「爆发」与「单日脉冲」一锅端 | 追了三天空气 |

本仓库不重新造雷达，**造雷达之上的对账层**。

## Architecture: 19 blanks × 3 layers = 57-piece spec

完整规格见 [`blanks_spec.json`](blanks_spec.json)（19 个空白技术点 × 采集/治理/消费三层）。状态诚实分级——**骨架不冒充完毕**：

- ✅ **8 engines done**（selftest 全绿：归一 / 证真 / 生命周期 / 词典治理 / 告警 / 一体查询 / 缓存 / 50例消歧基准）
- 🔧 **48 skeletons**（接口契约+断言规格内嵌，工厂 [`scaffold_gen.py`](scaffold_gen.py) 一键生成）
- 📐 路线图：[`pieces/_ROADMAP.json`](pieces/_ROADMAP.json)

Design principles: **stdlib-only**（零第三方依赖，clone 即跑）/ **deterministic**（同输入必同输出，可进 CI）/ **accountable**（每个数字一条命令复现，两轮原始数据保留——第一轮 harness 喂错形状、基准把作者自己抓了出来）。

## Platform model (how this becomes a platform)

| Mode | What | Feynman version | Status |
|---|---|---|---|
| **A · Upstream symbiosis** | PR to [new-term-radar](https://github.com/zhuyansen/new-term-radar) (751★): adopt TermLedger as its official identity layer | "The biggest class on campus uses our student-ID system" — zero-cost access to existing traffic | planned, PR draft in `pieces/upstream` |
| **B · OpenCore + subscription** | Engines open (MIT); premium alias dictionary + daily term-intel feed paid | "Student-ID system is free; the dedupe database is members-only" — plugs into our existing checkout funnel | funnel ready |
| **C · API** | `term_api` on free-tier HF Space / Workers, pay-per-query | "We don't sell the system, we sell swipes" | after A/B gain users |
| D · Standard (dark line) | The spec itself (`blanks_spec.json`) becomes the public "term identity" contract | "Every school prints student IDs in our format" | long-term, same play as the Ledger trilogy |

**推荐路径：A 引流 → B 收钱 → C 放大**，D 是副产品。

## Honest limits

- 证真层默认走 GitHub/HF 双源（经 `gh` CLI），离线时**降级标注 E?**，绝不静默造假
- 消歧基准 50 对为确定性生成用例，覆盖分隔符/大小写/全半角/版本负例/中文别名；真实流量语料需接 B01 采集层后扩展
- 中文别名词典现内置 6 组映射，欢迎 PR 扩充（过 `dict_govern` 环检测即可）

## Contact

📧 hcac4735@agent.qq.com ｜ License: [MIT](LICENSE)
