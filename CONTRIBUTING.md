# 如何贡献新 skill

## 一个 skill 的最小结构

```
skills/<skill-name>/
├── SKILL.md         必需
├── assets/          可选：HTML/CSS 模板、图片、配置文件等
└── references/      可选：长篇参考文档，Claude 按需加载
```

## `SKILL.md` 规范

必须以 YAML frontmatter 开头：

```markdown
---
name: skill-name
description: 一句话说清"这个 skill 在什么场景会被召回"。description 决定召回率，模糊等于没写。
---

# Skill 正文

## 何时使用

（触发条件、典型提问、关键字）

## 如何使用

（步骤、模板、示例）
```

**关键字段说明：**

| 字段 | 作用 | 建议 |
|---|---|---|
| `name` | skill 唯一标识，kebab-case | 和目录同名 |
| `description` | 语义召回依据 | 写清楚"什么场景 + 产出什么"，避免"帮助生成 XX"这类空话 |

## 本地验证

提交前务必跑一次本地加载测试：

```bash
ln -s "$(pwd)/skills/<skill-name>" "$HOME/.claude/skills/<skill-name>"
```

重启 Claude Code 会话，然后：
- 在 skill 列表里看到新 skill
- 用该 skill 的典型提问触发一次，确认召回和输出符合预期

## 命名建议

- 目录名 kebab-case：`html-report`、`boss-weekly`、`ad-review`
- 避免过于宽泛的名字：`data-analysis` 不如 `amc-campaign-review`
- 不要用团队成员姓名命名（成员会变动）

## 资源组织

- **`assets/`** 放会被 skill 直接读取、复制或引用的文件：HTML 模板、CSS tokens、图片、CSV 样例
- **`references/`** 放长文档：Claude 会按需加载，避免一次性塞满 context

## 提交前自检

- [ ] `SKILL.md` 含 frontmatter 的 `name` 和 `description`
- [ ] 本地 symlink 加载通过
- [ ] 没有硬编码密钥、内部 URL、个人邮箱
- [ ] 没有 `.DS_Store`、`__pycache__`、`.env` 等噪声
- [ ] README 里的 skill 列表同步更新
