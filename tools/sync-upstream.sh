#!/usr/bin/env bash
# 同步上游：fetch → 只把「我们自己的提交」rebase 到上游最新 → 校验 delta → 提示推送。
#
#   tools/sync-upstream.sh            正常同步
#   tools/sync-upstream.sh --dry-run  只看会做什么，不动仓库
#
# 依赖 fork/upstream-base.txt 记录「上次同步到的上游提交」。
# 为什么需要它：浅克隆里 merge-base 不准，普通 rebase 会把上游历史也重放一遍。
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/.."
ROOT=$(pwd)
DRY=0
[[ ${1:-} == --dry-run ]] && DRY=1

BASE_FILE="fork/upstream-base.txt"
DELTA_FILE="fork/delta.txt"

say() { printf '\n\033[1m%s\033[0m\n' "$*"; }
die() { printf '\033[31m错误：%s\033[0m\n' "$*" >&2; exit 1; }

# ---- 1. 前置检查 ----
say "1/5 检查工作区"
[[ -z $(git status --porcelain --untracked-files=no) ]] || die "工作区有未提交改动，先提交或 stash"
[[ -f $BASE_FILE ]] || die "缺少 $BASE_FILE（记录上次同步到的上游提交）"
BASE=$(tr -d ' \r\n' < "$BASE_FILE")
git cat-file -e "$BASE^{commit}" 2>/dev/null || die "记录的 base 提交 $BASE 不在本地历史里（浅克隆？先 git fetch --deepen=500）"
echo "   上次同步到：$BASE"

# ---- 2. 拉上游 ----
say "2/5 拉取上游"
if [[ $DRY -eq 1 ]]; then
  echo "   [dry-run] git fetch upstream main"
else
  git fetch --quiet upstream main
fi
UPSTREAM_TIP=$(git rev-parse upstream/main)
echo "   上游最新：$UPSTREAM_TIP"
if [[ $UPSTREAM_TIP == "$BASE" ]]; then
  echo "   已经是最新，无需同步"
  exit 0
fi

# ---- 3. rebase 我们自己的提交 ----
say "3/5 rebase 我们的提交到上游最新"
COUNT=$(git rev-list --count "$BASE..main")
echo "   会重放 $COUNT 笔提交"
if [[ $DRY -eq 1 ]]; then
  echo "   [dry-run] git rebase --onto upstream/main $BASE main"
  exit 0
fi

if ! git rebase --onto upstream/main "$BASE" main; then
  cat <<'EOF'

rebase 停在冲突上。处理方式：
  1. 编辑冲突文件，git add <文件>
  2. git rebase --continue
  3. 放弃：git rebase --abort

我们的改动只有 10 个文件，冲突通常出在：
  - app/pubspec.yaml          （已改为读 fork/version.txt，理论上不该再冲突）
  - app/lib/update/update_config.dart  （updateRepo 那一行）
  - runtime/build-runtime.sh  （proot pin 三行）
EOF
  exit 1
fi

# ---- 4. 校验 delta ----
say "4/5 校验我们的改动没有丢"
git diff --name-status upstream/main main | sed 's/\t/  /' > /tmp/dsh-go-delta.txt
if [[ -f $DELTA_FILE ]]; then
  if diff -q "$DELTA_FILE" /tmp/dsh-go-delta.txt >/dev/null; then
    echo "   delta 与 $DELTA_FILE 完全一致"
  else
    echo "   ⚠ delta 有变化（可能是有意新增的改动，也可能是上游覆盖）"
    diff -u "$DELTA_FILE" /tmp/dsh-go-delta.txt || true
    echo "   确认无误后：cp /tmp/dsh-go-delta.txt $DELTA_FILE"
  fi
else
  cp /tmp/dsh-go-delta.txt "$DELTA_FILE"
  echo "   已生成 $DELTA_FILE"
fi

echo "   提交数：$(git rev-list --count upstream/main..main) 笔"

# ---- 5. 记录新 base 并提示 ----
say "5/5 记录新的上游基点"
echo "$UPSTREAM_TIP" > "$BASE_FILE"
cat <<EOF

   fork/upstream-base.txt → $UPSTREAM_TIP

接下来：
   git add fork/ && git commit -m "chore(fork): 同步上游 $(echo "$UPSTREAM_TIP" | cut -c1-7) [skip ci]"
   git push origin main --force-with-lease

推送后去 Actions 看 Build APK (slim) 是否还绿。
EOF
