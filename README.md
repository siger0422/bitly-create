# bitly-create — Bitly 링크 단축 + UTM 자동화 스킬

조코딩ax용 Claude Code 스킬. 링크를 주면 ①플랫폼 ②게재위치 ③용도를 묻고, GA4 정합 UTM과
**비교가능한 제목**을 자동으로 채워 Bitly 단축 URL을 만든다. self-contained라 이 폴더 하나가 곧 배포 단위.

## 구성 (전부 이 폴더 안)
- `SKILL.md` — 스킬 정의 (경로는 스킬 base 디렉토리 기준 = 이식 가능)
- `conventions.md` — 플랫폼·UTM·제목·back-half 규칙 (스킬의 뇌, 팀 공통)
- `scripts/bitly.py` — create / list 실행기 (Python stdlib only, 의존성 0)
- `config.env.example` → 복사해서 `config.env` (토큰, ⚠️ gitignore)
- `install.sh` — ~/.claude/skills 연결 + 토큰 입력 + 검증

## 설치 (타 로컬에서)
```bash
git clone https://github.com/siger0422/bitly-create.git
cd bitly-create
./install.sh            # 심볼릭링크 연결 (+ 원하면 그 자리서 토큰 입력)
# 또는: ./install.sh copy   # 심볼릭링크 대신 복사 설치
```
- `~/.claude/skills/bitly-create` 가 이 레포를 가리키게 되고, 토큰은 `config.env`(레포 내, 커밋 안 됨)에 저장.
- install 시 토큰 입력은 **선택** — 건너뛰면 아래 "초기 설정 프롬프트"로 Claude Code에서 등록 가능.
- 규칙/스크립트 업데이트는 `git pull` 후 자동 반영(심볼릭링크) 또는 `./install.sh copy` 재실행.

## 🔑 초기 설정 — 신규 사용자용 프롬프트 (토큰+GUID)
스킬 연결 후, **팀 관리자에게 안전 채널(1Password 등)로 받은** 토큰·GUID를 채워 아래를 Claude Code에 붙여넣으세요:

```text
bitly-create 스킬 초기 설정해줘.
BITLY_TOKEN=여기에_받은_토큰_붙여넣기
BITLY_GROUP_GUID=여기에_받은_GUID_붙여넣기
```

→ 스킬이 토큰·그룹 유효성을 **검증**한 뒤 `config.env`에 저장(권한 600)하고, 계정·그룹명을 마스킹된 형태로
보고합니다. (CLI로는 `python3 scripts/bitly.py setup --token <T> --guid <G>` 와 동일.)
검증에 실패하면(401/403) 값을 다시 확인하세요. **모두 같은 공유 토큰**을 써야 전사 히스토리가 한곳에 모입니다.

## 사용
Claude Code에서:
- `이 링크 비틀리로 줄여줘 <URL>` / `/bitly-create <URL>` → 3가지 질문 후 생성
- `비틀리 목록 뽑아줘` → 전체 링크 md 표 (list 모드)

CLI 직접:
```bash
python3 scripts/bitly.py create --url "<URL>" --source linkedin --medium social \
  --campaign <slug> --content comment --title "[LinkedIn·댓글] 주제 · YYMMDD" [--back-half kw]
python3 scripts/bitly.py list --out links.md
```

## 전사 배포 & 히스토리 누적
- **모두가 같은 그룹 토큰**으로 만들면 `list` 한 번에 누가 만든 링크든 전부 md 표로 집계(Bitly 그룹=공유 원장).
  개인 토큰을 쓰면 그룹이 갈려 합산 불가 → **공유 그룹 토큰 1개 권장**.
- 정기 스냅샷은 `list --out links.md`를 주기 실행해 사내 위키/레포에 누적.

## 보안
`config.env` 토큰은 노출 금지(채팅·PR·공개 레포). 노출 시 Bitly에서 재발급 후 `config.env`만 교체.
