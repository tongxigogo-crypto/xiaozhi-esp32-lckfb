#!/bin/bash
# 三方协作守卫：开工前跑一次，不合规就别动手
# 用法:
#   ./scripts/agent_guard.sh            # 检查
#   ./scripts/agent_guard.sh --allow-dirty   # 只看基线，不拦 dirty

set -u
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO" || exit 1

ALLOW_DIRTY=0
[ "${1:-}" = "--allow-dirty" ] && ALLOW_DIRTY=1

BRANCH=$(git branch --show-current 2>/dev/null)
HEAD=$(git rev-parse --short HEAD 2>/dev/null)
DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || echo "")
REMOTE=$(git rev-parse --short "$UPSTREAM" 2>/dev/null || echo "?")

echo "分支     : $BRANCH"
echo "本地 HEAD: $HEAD"
echo "上游     : ${UPSTREAM:-未设置} ($REMOTE)"
echo "未提交   : $DIRTY 个文件"

BLOCK=0

if [ "$BRANCH" = "main" ]; then
    echo "警告     : 直接在 main 上作业，建议开分支"
fi

if [ "$DIRTY" -gt 0 ] && [ "$ALLOW_DIRTY" -eq 0 ]; then
    echo "阻断     : 工作区不干净，先提交或 stash，把基线固定下来"
    git status --porcelain | head -5
    BLOCK=1
fi

if [ "$HEAD" != "$REMOTE" ] && [ "$REMOTE" != "?" ]; then
    AHEAD=$(git rev-list --count "$REMOTE..HEAD" 2>/dev/null || echo "?")
    BEHIND=$(git rev-list --count "HEAD..$REMOTE" 2>/dev/null || echo "?")
    echo "提示     : 与上游不一致（领先 $AHEAD，落后 $BEHIND）"
fi

# 租约检查：PROJECT_STATE.md 里该区域是否被别人占着
STATE="$REPO/.agent/PROJECT_STATE.md"
if [ -f "$STATE" ]; then
    TAKEN=$(grep -E '^\| *(固件代码|表情资源)' "$STATE" | grep -v '空闲' | wc -l | tr -d ' ')
    if [ "$TAKEN" -gt 0 ]; then
        echo "提示     : 有区域被占用，确认不是你再去改："
        grep -E '^\| *(固件代码|表情资源)' "$STATE" | grep -v '空闲'
    fi
fi

if [ "$BLOCK" -eq 1 ]; then
    echo "结论     : 不可开工"
    exit 1
fi

echo "结论     : 可以开工（提交信息记得带 [agent:名字]）"
