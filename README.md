# Charles Skills

我自己写、每天在用的 Agent Skills。小而专一，可以组合使用，拿去改成你自己的版本。

> 别人写的、我推荐的 skills 在另一个仓库：[recommend-skills](https://github.com/Charlesxiaomi/recommend-skills)

## 安装

### Claude Code（插件方式，自动更新）

```bash
claude plugin marketplace add Charlesxiaomi/Charlesskills
```

```bash
claude plugin install charlesskills@charles
```

### 手动安装（复制单个 skill）

把 `skills/<分类>/<skill 名>/` 整个文件夹复制到 `~/.claude/skills/` 即可。

## Skills 清单

### 内容创作 · [content](./skills/content/README.md)

_暂无_

### 效率工具 · [productivity](./skills/productivity/README.md)

- [wechat-cli](./skills/productivity/wechat-cli/SKILL.md)：只读查询本机微信聊天记录、联系人、群成员、收藏等

### 工程开发 · [engineering](./skills/engineering/README.md)

_暂无_

### 测试中 · [in-progress](./skills/in-progress/README.md)

还在打磨、欢迎反馈的 skills，不随插件发布。

## 仓库结构

```
skills/
├── content/        内容创作（公众号、小红书等）
├── productivity/   日常效率工具
├── engineering/    写代码相关
├── in-progress/    测试中，不随插件发布
└── deprecated/     已停用
templates/          新建 skill 用的模板
scripts/            维护脚本
```

## License

[MIT](./LICENSE)
