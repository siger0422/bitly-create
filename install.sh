#!/usr/bin/env bash
# bitly-create 스킬 설치기
# - 이 레포 폴더를 ~/.claude/skills/bitly-create 로 연결(심볼릭링크, 기본)하거나 복사
# - config.env 가 없으면 공유 그룹 토큰을 입력받아 생성
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_DIR="${HOME}/.claude/skills"
TARGET="${SKILLS_DIR}/bitly-create"
MODE="${1:-link}"   # link(기본) | copy

echo "▶ bitly-create 설치"
echo "  레포: $REPO_DIR"
echo "  대상: $TARGET  (모드: $MODE)"

mkdir -p "$SKILLS_DIR"

# 기존 설치 정리
if [ -L "$TARGET" ] || [ -e "$TARGET" ]; then
  echo "  기존 $TARGET 제거"
  rm -rf "$TARGET"
fi

if [ "$MODE" = "copy" ]; then
  rsync -a --exclude '.git' --exclude 'config.env' --exclude 'links.md' "$REPO_DIR/" "$TARGET/"
else
  ln -s "$REPO_DIR" "$TARGET"
fi

# config.env (토큰) — 선택. 건너뛰면 Claude Code 프롬프트(모드 C)로 나중에 설정 가능.
CFG="$REPO_DIR/config.env"
if [ "$MODE" = "copy" ]; then CFG="$TARGET/config.env"; fi
if [ -f "$CFG" ]; then
  echo "  config.env 이미 존재 → 토큰 입력 생략"
else
  echo ""
  echo "  토큰 설정 방법 (둘 중 하나):"
  echo "   (A) 지금 터미널에서 입력  (B) 건너뛰고 Claude Code에서 설정 프롬프트로 입력"
  echo "  (토큰/GROUP_GUID는 팀 관리자에게 안전 채널로 전달받으세요)"
  read -rsp "  BITLY_TOKEN (건너뛰려면 Enter): " TOKEN; echo ""
  if [ -n "$TOKEN" ]; then
    read -rp  "  BITLY_GROUP_GUID: " GUID
    [ -z "$GUID" ] && { echo "  ❌ GROUP_GUID 비어있음"; exit 1; }
    python3 "$REPO_DIR/scripts/bitly.py" setup --token "$TOKEN" --guid "$GUID"
  fi
fi

# 검증 / 안내
echo ""
if [ -f "$CFG" ]; then
  echo "▶ 검증: list 모드 (최근 3건)"
  python3 "$REPO_DIR/scripts/bitly.py" list --size 3 --max 3 \
    || echo "  ⚠️ 검증 실패 — 토큰/네트워크 확인 (Claude Code 설정 프롬프트로 재설정 가능)"
  echo ""
  echo "✅ 설치 완료. Claude Code에서 \"이 링크 비틀리로 줄여줘\" 또는 /bitly-create <URL> 로 사용."
else
  echo "✅ 스킬 연결 완료 (토큰 미설정). Claude Code에 아래 프롬프트를 붙여 초기 설정하세요:"
  echo "   ─────────────────────────────────────────────"
  echo "   bitly-create 스킬 초기 설정해줘."
  echo "   BITLY_TOKEN=<받은 토큰>"
  echo "   BITLY_GROUP_GUID=<받은 GUID>"
  echo "   ─────────────────────────────────────────────"
fi
