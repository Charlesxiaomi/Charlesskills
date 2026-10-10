#!/usr/bin/env bash
set -euo pipefail

# 把本仓库的 skills 以软链接装到 ~/.claude/skills，之后 git pull 即可更新。
# 跳过 deprecated/。目标位置已有同名的非软链接文件夹时跳过，不覆盖。

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.claude/skills"

mkdir -p "$DEST"

while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$DEST/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "跳过 $name：$target 已存在且不是软链接"
    continue
  fi

  ln -sfn "$src" "$target"
  echo "已链接 $name"
done < <(find "$REPO/skills" -name SKILL.md -not -path '*/deprecated/*' -print0)
