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

# config.env (토큰)
CFG="$REPO_DIR/config.env"
if [ "$MODE" = "copy" ]; then CFG="$TARGET/config.env"; fi
if [ -f "$CFG" ]; then
  echo "  config.env 이미 존재 → 토큰 입력 생략"
else
  echo ""
  echo "  공유 Bitly 그룹 토큰을 입력하세요 (발급: https://app.bitly.com/settings/api/)"
  read -rsp "  BITLY_TOKEN: " TOKEN; echo ""
  read -rp  "  BITLY_GROUP_GUID [Bq4tcFdJw53]: " GUID; GUID="${GUID:-Bq4tcFdJw53}"
  printf 'BITLY_TOKEN=%s\nBITLY_GROUP_GUID=%s\n' "$TOKEN" "$GUID" > "$CFG"
  chmod 600 "$CFG"
  echo "  config.env 생성 완료"
fi

# 검증
echo ""
echo "▶ 검증: list 모드 (최근 3건)"
python3 "$REPO_DIR/scripts/bitly.py" list --size 3 --max 3 || {
  echo "  ⚠️ 검증 실패 — 토큰/네트워크 확인"; exit 1; }

echo ""
echo "✅ 설치 완료. Claude Code에서 \"이 링크 비틀리로 줄여줘\" 또는 /bitly-create <URL> 로 사용."
