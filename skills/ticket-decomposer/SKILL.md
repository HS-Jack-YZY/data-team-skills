---
name: ticket-decomposer
description: >
  GL.iNet 数据组对内执行 Plan 生成器：把已经过需求方反馈、范围已锁定的对外对齐报告
  （最新 alignment_v{N}.md，N≥2 表示已合并需求方反馈）拆分成可认领的工作单元清单（含输入 / 输出 / 工具 / 预计 h / DoD / 依赖 / 风险），
  并给出依赖图 + 工期估算（1 人串行 / 2 人并行 / N 人最大并行三档）+ 里程碑。
  组员据此并行执行；不替组员分配人名。

  仅在以下情况触发，否则不要加载：

  1. 用户显式调用 slash / @ 命令：
     - /data-team-skills:ticket-decomposer
     - @ticket-decomposer
     - /skill ticket-decomposer

  以下情况**不要触发**（让用户先明确意图）：
  - 用户只是描述需求或贴 ticket 文本但没显式喊本 skill —— 不要主动加载
  - 用户还没做对外对齐 / 还没合并反馈（ticket 目录下只有 alignment_v1.md，无更高 vN）—— 提示先用 ticket-aligner 跑反馈轮次
  - 用户在问"这个能不能做"等闲聊性问题
  - 用户要写报告本身（→ html-report）
  - 用户要写交付消息（→ delivery-message）
  - 数据本身的分析、SQL、可视化、口径解释

  本 skill 假设需求方已反馈、ticket 范围已锁定。如果还在对齐阶段请用 ticket-aligner。
allowed-tools: Read, Write, Bash
---

# ticket-decomposer — 对内执行 Plan 生成器

把"已对齐的需求"拆成"组员可抢单的工作单元"。每个单元 ≤ 8h、有 DoD、有工具、有依赖、不带人名分配。

整套数据组 ticket 处理 pipeline：

```
ticket → ticket-aligner（首次）→ alignment_v1.md → 发给需求方
                              ↓
                         需求方反馈
                              ↓
   ticket-aligner（再次喂入反馈）→ alignment_v2.md（… vN）
                              ↓
   ticket-decomposer（本 skill，自动读最新 vN）→ plan.md → 组员并行执行
```

---

## 怎么用（团队成员视角）

skill 通过 `data-team-skills` marketplace 自动同步。在 Claude Code 会话里**显式**触发：

| 触发方式 | 示例输入 |
|---|---|
| Slash 命令 | `/data-team-skills:ticket-decomposer` |
| `@` 引用 | `@ticket-decomposer 拆这个 ticket 的 Plan` |
| `/skill` 命令 | `/skill ticket-decomposer` |

**触发后 skill 会一次性问 2 件事**（编号是必须的，反馈摘要可选）：

```
请填以下 2 项：

1. ticket 编号 <如 66 或 DT-2026-0427-01> —— 本 skill 会自动在
   <编号>_<slug>/docs/alignment_docs/ 下找最新的 alignment_v{N}.md
2. 需求方反馈摘要（可选，如反馈点已合并进最新 vN 则跳过）:
```

skill 收齐后**自动定位最新 alignment_v{N}.md**（以下 shell 一行可达），产出**对内执行 Plan**，落盘到 `<编号>_<slug>/docs/plan.md`，并在对话中输出可复制的版本（前 3 章简短摘要 + 路径）。

```bash
# 找当前 ticket 目录最新 alignment 版本
TICKET_DIR=$(ls -d <编号>_*/ 2>/dev/null | head -n 1)
LATEST=$(ls "$TICKET_DIR/docs/alignment_docs/"alignment_v*.md 2>/dev/null \
         | sort -V \
         | tail -n 1)
```

如果 `$LATEST` 为空 / 只有 v1（说明还没合并需求方反馈）→ 触发前置检查报错，让用户先回 ticket-aligner 跑反馈轮次。

---

## 核心契约（Rev 2 · 不要违反）

1. **必须以最新 alignment_v{N}.md（反馈后版本，N≥2）为 source of truth** —— 不得绕过最新 vN 直接拆 ticket；最新 vN 不存在 / 仍是 v1 时**主动建议**先跑 ticket-aligner 完成反馈轮次，不硬拆
2. **工时与最新 alignment_v{N}.md 第三章选定档一致**（容差 ±10%）—— 例：最新 vN 选了"精准版 30h"，则 plan.md 总 h 必须在 27–33h 之间。不一致**不得**自行抹平，必须停下报错让用户重审 capabilities.md 或选定档
3. **每个工作单元 ≤ 8h** —— 超过就按维度（市场 / 关键词 / 章节）拆；下限 0.5h，低于不值得单列
4. **每个工作单元都有完整字段**：编号 / 单元名 / 输入 / 输出产物 / 预计耗时（h）/ 推荐工具 / 依赖 / 可并行兄弟 / DoD / 风险点。**没有 DoD 的 U 不算合格输出**
5. **依赖图无环** —— 检查 U 之间的依赖图，发现环立即报错
6. **不分配具体人名**（"@张三 接 U1"）—— skill 只列单元，分配在 IM 抢单或会上敲定
7. **alignment_v2 与现场说法冲突时停下** —— 不得自行调整；提示用户先回到 ticket-aligner 出 v3
8. **U 必须基于 work_unit_patterns.md 的 P1–P14 模板** —— 没合适 pattern 的自由格式 U，基线必须标 `（耗时待估）`
9. **plan.md 工时全用小时 h** —— 与 alignment_v2 + capabilities.md 单位一致；不混用工作日 / 天 / 半天等单位
10. **B 反推工具级时严格遵循 capabilities.md 基线** —— alignment_v2 是业务级描述，B 推到工具级时不要凭空给工具或工时；模糊到无法确定时回 alignment_v3

---

## 工作流（用户触发后按序执行）

### Step 1 — 输入捕获 + 前置检查

```bash
# 1. 用 ticket 编号定位 ticket 目录（前缀匹配）
TICKET_DIR=$(ls -d <编号>_*/ 2>/dev/null | head -n 1)

# 2. 找最新 alignment 版本
LATEST=$(ls "$TICKET_DIR/docs/alignment_docs/"alignment_v*.md 2>/dev/null \
         | sort -V \
         | tail -n 1)

# 3. 读最新版作为 source of truth
Read "$LATEST"
```

**前置检查（顺序执行，任一失败立刻停下报错）**：

1. ticket 目录不存在 / 找不到 `<编号>_*/` → 提示用户先跑 ticket-aligner（ticket-aligner 是 ticket 目录的 owner，本 skill 不创建目录）
2. 找到目录但 `docs/alignment_docs/` 下只有 `alignment_v1.md` → 提示"这是初版，未合并需求方反馈，请先回 ticket-aligner 跑反馈轮次产出 v2"
3. 最新 vN 第三章"时间预估"仍是**两档**（精准版 + 快速版同时存在，未收敛为单档）→ 提示"还没确认时间档位选哪个，请先回 ticket-aligner 让需求方选定档"
4. 最新 vN 第五章问答仍有未带 ✅ 标的项（说明需求方还没全部确认）→ 提示"还有 N 条问题未答复，请先回 ticket-aligner 完成对齐"
5. 最新 vN 提到"工具 / Dashboard"为主体的需求 → 提示"工具开发部分需另立项，本 skill 仅覆盖其中数据需求 / 复盘需求"

如果用户给了原 ticket 路径作为辅助（一般是 `$TICKET_DIR/docs/ticket.md`），可以 Read 一次作为业务背景（仅用于章节 1 引用 / 风险登记的语义补全），**不**用于决定范围。最新 alignment_v{N}.md 才是 source of truth。

### Step 2 — 读 capabilities.md（共享单源）

```
Read ../ticket-aligner/references/capabilities.md
```

加载工时基线 + 可行性锚点。**这是 alignment_v2 中工时数字的来源**——保证 plan.md 的 U 工时与 alignment 的 MVP 工时同源同基。

如果跨 skill 路径不可达（罕见），提示用户在 ticket-decomposer 下放一份 capabilities.md 副本，并加一条契约"两份 capabilities 必须保持一致"。

### Step 3 — 读 decomposition_recipes.md

```
Read references/decomposition_recipes.md
```

按 alignment_v2 顶层"类型分类"匹配配方。多类别 ticket → 取并集 + 去重（参考配方文末"多类别合并规则"）。

### Step 4 — 读 work_unit_patterns.md

```
Read references/work_unit_patterns.md
```

加载 14 个 U-pattern 模板，作为生成第 3 章 U 清单的填空池。

### Step 5 — 生成对内 Plan 文档

固定章节结构：

#### 顶层元信息

```
# 需求 {ticket_id} 对内执行 Plan

- **ticket 标题**：{从 alignment_v2 引用}
- **alignment 版本**：v2（基于：{文件路径}）
- **类型分类**：{从 alignment_v2 引用}
- **生成时间**：{YYYY-MM-DD HH:MM}
- **基于 capabilities.md 版本**：{version}
- **状态**：v1（首次拆分）
```

#### 章节 1：锁定的需求范围

从 **alignment_v2 第二章（我们计划这样做）+ 第三章（选定档 h + 覆盖范围）+ 第五章（已确认对齐项 ✅）+ 第六章（关于范围的几点说明）** 提取一段摘要，≤ 5 句话；让组员对得上对外承诺。

**关键**：因为 alignment_v2 是对外清爽报告，**不含** Tx 编号 / 🟢🟡🔴 / 工具级细节，B 必须根据这些业务级描述（"自家销售后台 / 公开评论 / 行业数据库"等）+ capabilities.md + decomposition_recipes.md **自己反推**：
- 业务级数据源 → 具体工具（"公开评论" → Apify Amazon 评论 / Reddit Scraper）
- 业务级范围 → 具体 ASIN / 关键词 / 时间窗
- 业务级输出 → 具体 U 序列

反推时**严格遵循 capabilities.md 基线**——不要凭空给工具或工时。如果 alignment_v2 描述模糊到无法确定具体工具，回到 alignment_v3 让 ticket-aligner 补充第二章的方法描述。

#### 章节 2：拆分思路

引用 decomposition_recipes.md 的"四步流程"框架，并说明本 ticket 选了哪些配方、为什么。多类别合并的去重 / 并集逻辑也在这里讲清楚。

#### 章节 3：工作单元清单

每个 U 一小节，按以下字段填空（来自 work_unit_patterns.md 的某个 P-pattern）：

```
### U{编号}. {单元名}

- **输入**：{...}
- **输出产物**：{...}
- **预计耗时**：{Xh}
- **推荐工具**：{...}
- **基于 P-pattern**：{P1–P14 中的某个，或"自定义"+ 标注耗时待估}
- **依赖**：{U 编号清单 / "无"}
- **可并行兄弟**：{U 编号清单}
- **DoD**：
  - {验收点 1}
  - {验收点 2}
- **风险**：{...}
```

#### 章节 4：依赖图

Markdown 缩进或简易箭头表（推荐 Mermaid，仅当组员习惯）。

```
U1 ─┐
U2 ─┼→ U5 → U6 → U7 → U8
U3 ─┤
U4 ─┘
```

**强制**：检查图无环。

#### 章节 5：工期估算

```
- **1 人串行**：Σ(所有 U) = {Xh}
- **2 人并行（典型）**：关键路径 = {Xh}
- **N 人最大并行（理论下限）**：{Xh}（N = {建议数}）
```

如果与 alignment_v2 第 6 章 MVP 总 h 偏差 > ±10%，**不得**自行抹平，输出 `⚠️ 工时不一致警告` 并提示用户检查。

#### 章节 6：里程碑 + DoD

整体交付物与验收标准，呼应 alignment_v2 第 6 章 MVP 承诺。每个里程碑写：

- 里程碑名
- 包含哪些 U
- 验收标准（行数 / 字段 / 报告章节完整度）

#### 章节 7：风险登记

总单元级风险汇总：

| 风险类型 | 触发的 U | 缓解措施 |
|---|---|---|
| 凭证依赖 | U_AMC, U_SPAPI | 抢单前 30 分钟内验证凭证 |
| 限流 | U_Reddit | 每批 ≤ 5 关键词 |
| 跨部门响应 | U_Attribution | 抢单时同步 IM 拉相关同事 |
| ... | ... | ... |

### Step 6 — 落盘

```
Write <编号>_<slug>/docs/plan.md
```

`<编号>_<slug>/` 是 ticket 目录（由 ticket-aligner 首次调用时创建）；plan.md 落盘到该目录的 `docs/` 直接下，与 `alignment_docs/` 同级。本 skill **不创建** ticket 目录骨架——ticket-aligner 是该目录的 owner。如果 ticket 目录不存在（即用户跳过了对齐直接拆 Plan），前置检查应该已经在 Step 1 报错；不应该走到这一步。

完成后在对话里**简短**告知文件路径 + 章节 5 工期估算摘要 + 章节 7 关键风险（≤ 3 条）。**不要**把整份 7 章节文档复读到对话里——已落盘，IM 用户拿路径打开即可。

---

## 反模式（Rev 2 · 这些情况不要做）

- ❌ 触发条件放宽到自然语言 —— 仅显式 slash / @ 命令
- ❌ alignment_v2 缺失 / 仍是 v1 / 第三章未收敛单档 / 第五章问答未全 ✅ 时硬拆 —— 主动建议回 ticket-aligner
- ❌ 绕过 alignment_v2 直接读 ticket 拆分 —— alignment_v2 是 source of truth；ticket 仅作业务背景辅助
- ❌ alignment_v2 与用户对话中说法冲突时自行调整 —— 必须停下让用户出 alignment_v3
- ❌ 工时与 alignment_v2 选定档（× 6h）不一致时自行抹平 —— 报错并提示用户重审 capabilities.md 或选定档
- ❌ **plan.md 出现"工作日 / 天 / 半天"作为工时单位** —— 全文统一用 h，与 capabilities.md / alignment_v2 单位一致
- ❌ alignment_v2 第二章业务级描述太模糊（如"做一些数据收集"），B 强行猜工具 —— 必须停下让 ticket-aligner 出 alignment_v3 补充第二章方法描述
- ❌ 单 U > 8h —— 必须按维度再拆
- ❌ 单 U 缺 DoD —— 不合格
- ❌ 依赖图成环 —— 报错
- ❌ 给单元强行配人名（"@张三 接 U1"）—— 只列单元
- ❌ 工具开发类 ticket 强行做完整 7 章节 Plan —— 提示拆分立项
- ❌ 在最终回复里把整份文档复读 —— 已落盘，给路径即可

---

## 文件结构

```
skills/ticket-decomposer/
├── SKILL.md                       # 你正在读的这个文件
├── references/
│   ├── decomposition_recipes.md   # 10 类 ticket 各自的拆分配方
│   └── work_unit_patterns.md      # 14 个 U-pattern 模板
└── assets/
    └── example_BE7200_plan.md   # 与 ticket-aligner 同 ticket 的下游 Plan 示例

# 共享文件（不在本 skill 目录内）：
../ticket-aligner/references/capabilities.md   # 单源工时基线
```

落盘根目录约定（ticket 目录由 ticket-aligner 首次调用时创建；本 skill 只往 `docs/plan.md` 写）：

```
<编号>_<slug>/                                  # ticket 根
└── docs/
    ├── ticket.md                               # 原 ticket 归档
    ├── alignment_docs/
    │   ├── alignment_v1.md                     # ticket-aligner 首次输出
    │   └── alignment_v{N}.md                   # 反馈后（再次调用 ticket-aligner） · 本 skill 必读最新 vN
    └── plan.md                                 # 本 skill 输出
```

---

## 一句话工作流摘要

> 收齐 3 个槽位 → 前置检查（alignment_v2 存在 + 假设全确认 + 不是工具开发）→ 读 capabilities + recipes + patterns → 按 7 章节骨架填，工时与 alignment_v2 一致 ±10% → 检查依赖图无环 → 落盘 plan.md → 在对话里给路径 + 工期摘要 + Top 3 风险。
