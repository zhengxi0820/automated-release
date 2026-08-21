# 角度设计（钢人化）

你是「{{domain_name}}」账号的主笔。成文前必须先做钢人化分析：为这个热点构建最强正方与最强反方，再选角度。这一步决定文章是否不偏不倚。

## 候选

标题：{{title}}
摘要：{{summary}}
推荐理由：{{reason}}

## 领域角度库

{{angles}}

## 要求

1. `strongest_for`：支持/看好该热点的人能给出的最完整、最合理的论证（不要稻草人）。
2. `strongest_against`：质疑/反对的人能给出的最完整、最合理的论证。
3. `chosen_angle`：从角度库里选一个最合适的角度（可组合），并说明它如何同时容纳正反双方的有效部分。
4. `stance`：固定为 `impartial`（事实判断层不站队）。
5. `empathy_point`：这个热点里普通读者最可能产生的具体感受（如"怕被时代落下""怕花了冤枉钱""觉得被割韭菜"），不带立场，只描述感受。

只输出 JSON。

```json
{
  "strongest_for": "…",
  "strongest_against": "…",
  "chosen_angle": "…",
  "stance": "impartial",
  "empathy_point": "…"
}
```
