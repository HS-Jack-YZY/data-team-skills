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
    └── html-report/         GL.iNet 数据组的 HTML 报告模板与设计系统
```

## 安装使用

```bash
# 1. clone 到本地任意位置
git clone git@github.com:HS-Jack-YZY/data-team-skills.git
cd data-team-skills

# 2. 把想用的 skill 软链到 Claude Code 的 skills 目录
ln -s "$(pwd)/skills/html-report" ~/.claude/skills/html-report

# 3. 重启 Claude Code 会话，skill 即可被加载
```

想一次性启用全部 skill：

```bash
for d in skills/*/; do
  name=$(basename "$d")
  ln -s "$(pwd)/$d" "$HOME/.claude/skills/$name"
done
```

## 贡献新 skill

见 [CONTRIBUTING.md](./CONTRIBUTING.md)。简而言之：一个 skill 一个目录，含 `SKILL.md`（带 frontmatter 的 `name` 和 `description`），大资源放 `assets/`，长文档放 `references/`。

## License

MIT — 见 [LICENSE](./LICENSE)。
