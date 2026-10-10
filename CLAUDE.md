本仓库存放 Charles 自己编写的 Agent Skills。

## 分类

skills 按分类放在 `skills/` 下：

- `content/`：内容创作（公众号、小红书、视频等）
- `productivity/`：日常效率工具
- `engineering/`：写代码相关
- `in-progress/`：测试中，公开但不随插件发布
- `deprecated/`：已停用

`content/`、`productivity/`、`engineering/` 是**正式分类**。

## 新增或修改 skill 时必须同步

1. 从 `templates/example-skill/` 复制一份到对应分类，文件夹名即 skill 名（小写、连字符）。
2. 正式分类里的 skill，必须同时：
   - 在顶层 `README.md` 的对应分类下加一行，skill 名链接到它的 `SKILL.md`；
   - 在该分类的 `README.md` 里加一行一句话介绍；
   - 在 `.claude-plugin/plugin.json` 的 `skills` 数组里加上路径。
3. `in-progress/` 和 `deprecated/` 里的 skill 只写进各自分类的 `README.md`，不进顶层 README 和 `plugin.json`。
4. skill 移动分类、改名、删除时，以上三处一起改。

## 维护脚本

- `scripts/list-skills.sh`：列出仓库里所有 `SKILL.md`。
- `scripts/link-skills.sh`：把正式分类和 `in-progress/` 的 skills 以软链接装到 `~/.claude/skills`，之后 `git pull` 即可更新。
