# 写作 Skill 说明（style_core 设计文档）

> 2026-09 重构。调研了 4 路来源后重写：GitHub 开源写作 skill 生态、Anthropic/OpenAI 官方提示工程文档与英文 anti-slop 社区、本地写作 skill（khazix-writer、Matt Pocock writing 套件）、中文小红书开源 prompt 生态。原始调研材料在 `.research/`（未入库）。

## 结构

```
prompts/
├── style_core.md      # 共享写作技法核心（写作 skill 主体），注入下方两个成文模板
├── write.md           # 热点评论文（引用 {{style_core}}）
├── concept_write.md   # 概念科普文（引用 {{style_core}}）
└── …                  # assess/research/steelman/polish/cardify 不变
```

`pipeline/stages/write.py` 模块级加载 `style_core.md` 为 `STYLE_CORE`，write / concept_write 两个 stage 注入 `{{style_core}}` 占位符。单源维护，改技法核心两处生效。

## 痛点与对策

| 旧提示词的问题 | 新设计 | 依据 |
|---|---|---|
| 以负面清单为主（禁用词、禁标点），正面技法指导薄 | 技法核心以正向技法为主体（节奏、具体性、开头菜单、扣主线句），负面清单收缩为 11 条数据确认项，每条附替换方案 | Anthropic 官方（正向指令优于禁令、范例优于禁止）；禁令会被"表演式遵守"（Sam Kriss/NYT）；负面清单越长越容易自相矛盾（GPT-5 指南） |
| 禁了一些"伪 AI 味" | 移除对"首先/其次"（正文级）、排比、比喻、问句、被动句的禁令——对照语料实测人类同样高频，禁了反而伤 | lieflat-less-ai-tone 283 万字对照语料的"不作为改写理由"表 |
| concept_write 把寓言五段式写死 | 第一步改为"选叙事载体"：寓言/场景推演/反直觉现象/历史事件/思想实验五选一，按概念特性判断；结构纪律保留但 reveal 位置由"读者已看见机制"决定（40-60% 浮动） | khazix-writer 原型库思想 + Matt Pocock 的 grounding 系统（概念先铺垫后使用） |
| 热点文无结构指导 | 原型菜单（反差解读/算账/影响推演/避坑指南）+ 共同纪律（开头钩子、正反论证、对立面承认、轻收尾） | khazix-writer 五原型 + writing-shape"开头即 contract" |
| 标题自由生成 | 公式检索+填槽（分热点组/科普组），张力 ≥2 检查，标题或首句含核心关键词 | dbs-xhs-title 75 公式库、xhs-ai-tools-writer |
| self_check 是 pass/fail 摆设 | band 制（strong/moderate/weak）+ 四测（删除测试、可移植性测试、节奏测试、红线测试）+ 分诊（有观点被埋住→改写；空洞→删，不许编） | de-slop rubric、petergyang/no-ai-slop eval、khazix-writer 四层自检 |
| 段落长度约束有、功能约束无 | "一段只做一个动作，做完就停"（beat 思想）；句长方差（禁连续三句同长，最可测的机器信号） | writing-beats、jalaalrd/anti-ai-slop-writing |
| 无记忆点概念 | 动笔前先定"记忆点"（leading word），标题和转场从它生成 | writing-fragments、小红书标题生态 |
| 具体性压力可能逼模型编造 | 具体性纪律与诚实红线配对："素材缺例证→砍论点或降级为推测，不许编" | de-slop "flag hollow, don't fabricate"、conorbronsdon "Never inject these" |

## 保留的旧规则（依然有效）

- 事实账本 / todo_verify 事实铁律（research.md + write.md）
- 禁止编造亲历 + 机检（`FABRICATED_PATTERNS` 正则，命中即低温重写）——机检前置是英文圈共识（Simon Willison / de-slop）
- 概念文的零门槛、数字自洽（心算验算、数量级拉开）、第一性原理、讲透不留尾
- 人设外置（domains/*/persona.md），且明确"人设与技法核心冲突时以人设为准"（voice samples 覆盖规则，blader/humanizer）

## 后续飞轮（未实现，按优先级）

1. **对照范文库**：人工改稿时把「AI 初稿 / 定稿 / 差异归因」存档，积累 20-30 组后作为 few-shot 注入（khazix-writer style_examples 第 12 板块的做法，信号密度最高的风格教材）。
2. **改稿 diff 回流**：只 diff 首尾两版，多次出现的修改自动进技法核心，单次出现存档观察（jzOcb/writing-style-skill 的 P0/P1/P2 置信度分级）。
3. **中文 AI 词表自建**：用我们自己成稿跑词频统计，替换通用清单里的词表部分（jalaalrd 的方法论）。
4. **AI 痕迹机检扩展**：把 11 条高置信痕迹中的机械可查项（破折号计数、提示语冒号、翻案腔正则、相邻句同构）做成 `check_prose.py` 式的代码检查，放进 stage 后处理。

## 主要参考

- anthropics/skills · doc-coauthoring（无上下文读者测试、删减优先闸门）
- mattpocock/skills · writing-fragments / writing-beats / writing-shape（leading word、grounding、beat、format arguments）
- KKKKhazix/khazix-skills · khazix-writer（原型库、技法三元组、四层自检、诚实性红线、AI 初稿 vs 定稿对照示例）
- larashero3-dotcom/lieflat-less-ai-tone（283 万字对照语料、11 条高置信 AI 痕迹及倍率、"不作为改写理由"反证表）
- Raymondhou0917/speak-human-tw（38 种 AI 痕迹全景、假人味四防、"先删再具体化再降格式"）
- yanhua1010/self-media-content-workflow（去模板化审校 4:1 正负比、标题漏斗、证据包纪律）
- jzOcb/writing-style-skill（Voice Dimensions 量化、改稿数据飞轮）
- petergyang/no-ai-slop、blader/humanizer、jalaalrd/anti-ai-slop-writing、isatimur/de-slop、conorbronsdon/avoid-ai-writing（可移植性测试、样本覆盖规则、句长方差、band rubric、修订循环、防 humanizer 腔）
- dbs-xhs-title / mini20201314-crypto/xhs-ai-tools-writer / EBOLABOY/xhs-ai-writer / OrangeViolin/content-pipeline（标题公式制、科技干货派骨架、段落随机化、钉子段、tag 公式）
- Anthropic Prompting best practices / Prompting Claude Fable 5.1 § Writing density（正向指令、定义式反模式、范例+rationale）
- SELF-REFine (arXiv:2303.17651)、Chain of Density (arXiv:2309.04269)
