# data-team-skills

GL.iNet 数据组共用的 Claude Code Skills 与 Commands 合集。

## 这是什么

一个公开的 Claude Code [Skills](https://docs.claude.com/en/docs/claude-code/skills) 与 [Slash Commands](https://docs.claude.com/en/docs/claude-code/slash-commands) 仓库，汇总数据组日常工作中反复用到的模板、报告风格、分析流程，以及共享的 slash command。任何装了 Claude Code 的人都可以通过 plugin marketplace 一键安装（推荐），或 clone 后手工挂载 `skills/` / `commands/` 到 `~/.claude/`。

## 目录

```
.
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── .gitignore
├── skills/
│   ├── html-report/                GL.iNet 数据组的 HTML 报告模板与设计系统
│   ├── delivery-message/           GL.iNet 数据组对外交付的标准发布消息模板
│   ├── ticket-aligner/             ticket 对外对齐报告生成器
│   ├── ticket-decomposer/          对外对齐报告 → 对内执行 Plan
│   └── social-reviews-analyzer/    Reddit / Discourse / Amazon 评论 CSV → 用户画像 + 痛点 CSV
└── commands/
    ├── translate-manual.md         英文 → 德/法/西/波兰语 产品手册翻译（v2.1 单 agent 决策固化）
    └── translate-compare.md        多 agent 翻译 + 跨语言一致性协调（v2.1 多 agent 编排）
```

## 标准工作流（GL.iNet 数据组）

下面是数据组用本仓库 5 个 skill 处理一个 ticket 的端到端流程。每一步的产出位置都已硬编码进对应 SKILL.md，**无需配置**——目录约定即配置。

### 0. 起点

其他部门提一个 ticket。在数据组 ticket 工作根目录（建议数据组共享的 ticket 工作区）打开 Claude Code。

### 1. 对齐（`/ticket-aligner <编号>` + ticket 内容）

```bash
/ticket-aligner 66 ./inbox/manual-sft1200-translation.txt
```

skill 会：

- 自动派生 slug（如 `Manual-SFT1200-Translation-FR-DE-ES-PL`）
- 创建 ticket 根目录 `66_<slug>/`
- 把原始 ticket 写到 `66_<slug>/docs/ticket.md`
- 生成第一版对齐报告 → `66_<slug>/docs/alignment_docs/alignment_v1.md`
- 在终端输出"四件套"（路径 / 章节五节选 / 组员 SOP / 对齐确认私信）

> **必须**附编号。未附时 skill 会停下问你要——不会自己编。

### 2. 反馈轮次（重复 `/ticket-aligner`）

需求方反馈后再次调用本 skill，会自动在同目录里写出 `alignment_v2.md`、`alignment_v3.md`……版本号 +1，旧版本永远保留（需求方溯源 + 内部审计依据）。

### 3. 拆解（`/ticket-decomposer <编号>`）

```bash
/ticket-decomposer 66
```

skill 自动定位最新 `alignment_v{N}.md`（一行 `ls ... | sort -V | tail -1` 解决），产出执行 plan：

```
66_<slug>/docs/plan.md
```

### 4. 数据获取与分析（中间步骤）

数据采集、清洗、分析在 `66_<slug>/docs/data/` 下进行。其中：

- **`/social-reviews-analyzer`**：scratch 中间产物（`units.jsonl` / `analyses.jsonl`）放在 `docs/data/scratch/`（建议加进 `.gitignore`），最终样本 CSV 落 `docs/data/<merged>.csv`
- 其他自定义数据脚本：约定也放在 `docs/data/` 下

### 5. 报告（`/html-report`）

最终 HTML 报告落在 ticket **根目录**（不在 `docs/` 下）：

```
66_<slug>/66_<slug>.html               # 单文件（默认）
66_<slug>/66_<slug>/index.html         # 带 assets/data 时降级到同名子目录
```

放在 ticket 根的语义：**这是可对外发的成品**——和 `docs/` 下的过程材料一眼区分。

### 6. 发布消息（`/delivery-message`）

skill 输出**可直接复制**的钉钉消息正文（对话给文本，复制即发），同时镜像写到 `66_<slug>/docs/delivery.md` 留档。

### 7. 在钉钉上交付

复制 skill 的对话输出，发到对应群。

---

### 一个完成态 ticket 的完整目录长这样

```
66_Manual-SFT1200-Translation-FR-DE-ES-PL/
├── docs/                                       ← 过程性文档
│   ├── ticket.md
│   ├── alignment_docs/
│   │   ├── alignment_v1.md
│   │   ├── alignment_v2.md
│   │   └── alignment_v3.md
│   ├── plan.md
│   ├── data/
│   │   ├── reddit_merged.csv
│   │   └── scratch/                            ← gitignored
│   └── delivery.md
└── 66_Manual-SFT1200-Translation-FR-DE-ES-PL.html  ← 交付物（在 ticket 根）
```

整个目录可以独立打包归档——一个 ticket 完成后，这一个文件夹就是它的全部上下文，无跨目录依赖。

### 设计哲学

- **过程 vs 成品 用文件位置区分**：`docs/` 下都是给组内看的中间材料；ticket 根目录下的 `.html` 是可对外发的成品
- **版本演进 用文件名区分**：alignment 用 `_v1` / `_v2` / `_v3` 后缀，每次反馈轮次保留历史；plan / delivery / report 是当前快照（重写覆盖）
- **路径约定即配置**：5 个 skill 都按 `<编号>_<slug>/...` 这个模式硬编码路径，不读环境变量、不读配置文件——约定优于配置
- **一个 ticket 一个 owner**：ticket 目录由 `ticket-aligner` 首次调用时创建；后续 skill 只往已有目录里加文件，**不**自己创建新 ticket 目录骨架

---

## 安装使用（Claude Code 插件 marketplace 模式）

本仓库同时是一个 **Claude Code 插件 marketplace**——两条命令装完，之后自动更新。

```
/plugin marketplace add HS-Jack-YZY/data-team-skills
/plugin install data-team-skills@data-team-skills
```

就这些。重启 Claude Code 会话后，`skills/` 与 `commands/` 下的全部条目都可用。

**后续怎么更新？** 什么都不用做。每次启动新会话时，Claude Code 会刷新 marketplace；我们这边 push 的任何 skill / command 改动或新增都会自动同步到你本地。

**想关掉自动更新？** 编辑 `~/.claude/plugins/known_marketplaces.json`，把 `data-team-skills` 条目的 `"autoUpdate"` 改为 `false`，改用手动：

```
/plugin marketplace update data-team-skills
```

### 触发翻译命令（commands）

装好后在任意会话里直接打：

```
/data-team-skills:translate-manual ./MT6000-English.md German
/data-team-skills:translate-compare ./MT6000-English.md German French Spanish
```

- `translate-manual`：单 agent，按 v2.1 硬编码决策直接出一版翻译，适合内部速翻。
- `translate-compare`：每语言 spawn 3 个 agent（2 Sonnet + 1 Opus）+ Opus merger + 跨语言协调，适合发布版高质量翻译。N 个目标语言 = `4N + (N>1 ? 1 : 0)` 个 agent。

参数固定为"源文件路径 + 目标语言"。**不会**停下来询问 UI 字符串、术语、合规、排版——所有决策在命令里硬编码。决策来源（v2.0 product team Q1–Q18 + v2.1 specialist agents Q19–Q24，2026-04-29）由 maintainer 私存，不随 marketplace 分发；如需翻阅细节联系 GL.iNet 数据组 maintainer。

### 从旧的手工 symlink 方式迁移

如果你之前按旧 README 手工 `ln -s` 过 `~/.claude/skills/html-report`，装 plugin **之前**先删掉那个 symlink，避免同名 skill 冲突：

```bash
rm ~/.claude/skills/html-report
```

然后再走上面两条 `/plugin` 命令。

### 不想用插件系统？传统 clone + symlink 仍然可用

```bash
git clone git@github.com:HS-Jack-YZY/data-team-skills.git
cd data-team-skills
ln -s "$(pwd)/skills/html-report" ~/.claude/skills/html-report
```

这种方式不会自动更新；每次要同步上游改动需手动 `git pull`。

## 贡献新 skill

见 [CONTRIBUTING.md](./CONTRIBUTING.md)。简而言之：一个 skill 一个目录，含 `SKILL.md`（带 frontmatter 的 `name` 和 `description`），大资源放 `assets/`，长文档放 `references/`。

> ⚠️ **关键一步（仅适用于 skill）**：新增 **skill** 后必须把路径同步追加到 `.claude-plugin/marketplace.json` 的 `plugins[0].skills` 数组，否则已安装的同事不会收到。skills 走显式注册——这是有意设计，便于控制哪些 skill 暴露给团队。
>
> **commands 走自动发现**，无需 manifest 注册：把 `<command-name>.md`（带 frontmatter 的 `name` 与 `description`）扔到 `commands/` 目录即可，Claude Code 插件 loader 会自动加载。本 marketplace 这样设计是因为 Claude Code plugin schema 不接受 `plugins[].commands` 字段（实测：5 个参考 marketplace 共 150+ plugins 零声明）。

## License

MIT — 见 [LICENSE](./LICENSE)。
