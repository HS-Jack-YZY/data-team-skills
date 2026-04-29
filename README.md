# data-team-skills

GL.iNet 数据组共用的 Claude Code Skills 合集。

## 这是什么

一个公开的 Claude Code [Skills](https://docs.claude.com/en/docs/claude-code/skills) 仓库，汇总数据组日常工作中反复用到的模板、报告风格、分析流程等。任何装了 Claude Code 的人都可以 clone 后直接把 skill 挂到自己的 `~/.claude/skills/` 使用。

## 目录

```
.
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── .gitignore
└── skills/
    ├── html-report/                GL.iNet 数据组的 HTML 报告模板与设计系统
    ├── delivery-message/           GL.iNet 数据组对外交付的标准发布消息模板
    ├── ticket-aligner/             ticket 对外对齐报告生成器
    ├── ticket-decomposer/          对外对齐报告 → 对内执行 Plan
    └── social-reviews-analyzer/    Reddit / Discourse / Amazon 评论 CSV → 用户画像 + 痛点 CSV
```

## 安装使用（Claude Code 插件 marketplace 模式）

本仓库同时是一个 **Claude Code 插件 marketplace**——两条命令装完，之后自动更新。

```
/plugin marketplace add HS-Jack-YZY/data-team-skills
/plugin install data-team-skills@data-team-skills
```

就这些。重启 Claude Code 会话后，`skills/` 下的全部 skill 都可用。

**后续怎么更新？** 什么都不用做。每次启动新会话时，Claude Code 会刷新 marketplace；我们这边 push 的任何 skill 改动或新增都会自动同步到你本地。

**想关掉自动更新？** 编辑 `~/.claude/plugins/known_marketplaces.json`，把 `data-team-skills` 条目的 `"autoUpdate"` 改为 `false`，改用手动：

```
/plugin marketplace update data-team-skills
```

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

> ⚠️ **关键一步**：新增 skill 后必须把路径同步追加到 `.claude-plugin/marketplace.json` 的 `plugins[0].skills` 数组，否则已安装的同事不会收到。本 marketplace 走显式注册，不会按目录自动扫描——这是有意设计，便于控制哪些 skill 暴露给团队。

## License

MIT — 见 [LICENSE](./LICENSE)。
