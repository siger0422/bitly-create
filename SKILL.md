---
name: bitly-create
description: >
  사용자가 링크를 주면 Bitly 단축 URL + GA4 분석용 UTM을 자동 설정해 생성해주는 스킬.
  "링크 단축", "비틀리", "bitly", "단축 url", "utm 붙여서", "이 링크 줄여줘", "댓글에 올릴 링크",
  "링크 줄여줘", "shorten link", "비틀리 목록/히스토리/내역 뽑아줘" 요청 시 사용.
  링크의 플랫폼·트래킹·용도 3가지를 묻고, 도착지 콘텐츠를 파악해 source/medium/campaign/content와
  비교가능한 제목까지 알아서 채워 Bitly에서 생성한다. list 모드로 전체 링크 히스토리를 md 표로도 출력.
---

# bitly-create

링크를 받아 **GA4 정합 UTM + 식별 가능한 제목**으로 Bitly 단축 URL을 만든다.

> **경로 규칙(이식성)**: 이 스킬은 self-contained다. 모든 파일은 **이 스킬의 base 디렉토리**
> 안에 있다. 호출 시 주어지는 "Base directory for this skill: …" 경로를 `SKILL_DIR`로 삼아
> 아래 명령의 `$SKILL_DIR`를 그 절대경로로 치환해 실행한다. (예: `~/.claude/skills/bitly-create`)

## 컨텍스트 (작업 시작 시 반드시 읽기)
- 규칙 SSOT: `$SKILL_DIR/conventions.md` — 플랫폼표·UTM·제목·back-half 규칙
- 실행기: `$SKILL_DIR/scripts/bitly.py` (토큰/그룹은 `$SKILL_DIR/config.env` 또는 환경변수에서 자동 로드)

> `config.env`가 없으면 미설치 상태. 사용자에게 `$SKILL_DIR/install.sh` 실행(또는 `config.env`에
> `BITLY_TOKEN`/`BITLY_GROUP_GUID` 입력)을 안내한다.

---

## 모드 A — 링크 생성 (기본)

### 1단계: 3가지 질문 (AskUserQuestion으로 한 번에)
사용자가 **이미 일부를 말했으면 그 값은 묻지 말고 채택**하고, 빠진 것만 묻는다.

1. **어떤 플랫폼?** — LinkedIn / Instagram / Threads / X / YouTube / 네이버블로그 / Slack / KakaoTalk / Email
   → `conventions.md` 표 1로 source·medium 결정.
2. **어떤 데이터를 트래킹? (게재 위치)** — 본문 / 댓글 / 바이오 / 스토리 / DM / 영상설명 …
   → 표 2로 utm_content 결정. (medium은 항상 채널 카테고리. 위치는 content로!)
3. **용도?** — 한 줄로 (예: "신규 글 홍보 댓글", "프로필 상시 링크"). 캠페인/제목 톤 판단에 사용.

추가로 **back-half(custom 키워드)**는 항상 묻는다(월 100개 한도). "랜덤이면 엔터" 식으로.

### 2단계: 도착지 콘텐츠 파악
- WebFetch로 도착지 URL의 제목/h1 추출 → **주제요약(한글 6~14자)** 압축. 회사명·공통 꼬리표 제거.
- 봇 차단(403)·SPA로 제목이 안 나오면: 브라우저 UA로 curl 재시도 → 그래도 안 되면 URL 슬러그에서
  추론하거나 사용자에게 주제 한 줄 확인.

### 3단계: 값 조립 (conventions.md 그대로)
- `utm_campaign`: 도착지 슬러그 우선 (예: `hackathon-edu`).
- `utm_content`: 표 2 값.
- **제목**: `[{플랫폼}·{위치}] {주제요약} · {YYMMDD}` (40자 이내, 오늘 날짜는 env의 currentDate 사용).

### 4단계: 생성
```bash
python3 "$SKILL_DIR/scripts/bitly.py" create \
  --url "<원본URL>" \
  --source <src> --medium <med> --campaign <slug> --content <placement> \
  --title "<생성한 제목>" \
  [--back-half <keyword>] [--tags <a,b>]
```
스크립트가 JSON(link/title/long_url) 반환. `warn` 필드 있으면 사용자에게 그대로 전달.
(back-half를 쓰면 스크립트가 부모 hash를 자동 archive해 목록을 1줄로 정리한다 — conventions.md §6 참고.)

### 5단계: 보고
- 단축 링크(복사용), 최종 UTM URL, 제목, GA4에서 어떻게 잡히는지(source/medium/campaign/content) 한 줄 요약.

---

## 모드 B — 히스토리/목록 (list)
"비틀리 목록/내역/히스토리 뽑아줘", "지금까지 만든 링크" 요청 시:
```bash
python3 "$SKILL_DIR/scripts/bitly.py" list                       # stdout 표
python3 "$SKILL_DIR/scripts/bitly.py" list --out "$SKILL_DIR/links.md"   # 파일 저장
```
같은 그룹 토큰이면 **전사 누가 만든 링크든 전부** 집계된다(공유 원장). 제목 규칙 덕에 한눈에 비교 가능.

---

## 가드레일
- Tags·QR은 **기본 off**. 사용자가 명시 요청할 때만.
- `utm_medium`에 절대 "comment/video/bio" 같은 위치를 넣지 않는다(GA4 채널 깨짐). 위치는 content.
- 토큰은 config.env/환경변수에만. 채팅/PR/커밋에 출력 금지.
- back-half는 한도 있으니 항상 사용자 확인.
