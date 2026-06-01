# Bitly 링크 단축 + UTM 컨벤션 (조코딩ax SSOT)

`bitly-create` 스킬이 참조하는 규칙. 여기를 고치면 스킬 동작이 바뀐다.

---

## 0. 핵심 원칙 — GA4 정합

`utm_medium`에는 **채널 카테고리만**(social / email / referral / cpc …) 넣는다.
"댓글·본문·바이오·영상설명" 같은 **게재 위치는 `utm_medium`이 아니라 `utm_content`**로 보낸다.

> ⚠️ 과거 링크 일부는 `utm_medium=comment`, `utm_medium=vedio(오타)` 처럼 위치/오타를 medium에 넣어
> GA4 기본 채널 그룹(Organic Social)에서 누락됐다. 스킬은 이를 **표준화**한다. 과거 링크와 medium 값이
> 달라 보이는 건 의도된 정정이다.

---

## 1. 플랫폼 → source / medium 매핑

| 플랫폼 | utm_source | 기본 utm_medium | 비고 |
|---|---|---|---|
| LinkedIn | `linkedin` | `social` | |
| Instagram | `instagram` | `social` | 바이오 링크면 content=`bio` |
| Threads | `threads` | `social` | |
| X (Twitter) | `x` | `social` | |
| YouTube | `youtube` | `social` | 댓글/영상설명은 content로 구분 |
| 네이버 블로그 / 외부 블로그 | `naverblog` (또는 `blog`) | `referral` | 자사 글을 블로그 본문에 임베드 |
| Slack | `slack` | `referral` | 사내 공유 |
| KakaoTalk (채널/메시지) | `kakao` | `referral` | |
| Email / 뉴스레터 | `email` | `email` | |

신규 플랫폼은 이 표에 행을 추가하면 된다.

## 2. utm_content — 게재 위치(placement)

| 위치 | utm_content |
|---|---|
| 게시물 본문 | `post` |
| 댓글 | `comment` |
| 고정 댓글 | `pinned-comment` |
| 프로필/바이오 링크 | `bio` |
| 스토리 | `story` |
| DM | `dm` |
| 영상 설명란 | `video-desc` |
| 영상 자막/카드 | `video-card` |

A/B 소재 구분이 필요하면 `comment-a` / `comment-b` 처럼 접미사.

## 3. utm_campaign

- 도착지 글의 **슬러그를 그대로** 쓰는 게 1순위 (예: `hackathon-edu`, `spigen-ax-training`).
- 슬러그가 없으면 `주제-YYMM` (예: `ax-solo-2606`).
- 같은 콘텐츠를 여러 플랫폼에 뿌리면 **campaign은 동일**하게 유지 → GA4에서 캠페인 단위로 합산, 플랫폼별 비교는 source로.

## 4. utm_term

- 보통 비움. 유료 검색/키워드 타겟일 때만 키워드.

---

## 5. 제목(Title) 규칙 — "히스토리"의 본체

Bitly Links 목록에서 **제목만 보고 비교·식별**되도록. 도착지 페이지 `<title>`을 그대로 쓰면
"조코딩 AX 파트너스"처럼 다 똑같아져서 못 쓴다. 아래 **압축 포맷**으로 생성한다.

```
[{플랫폼}·{위치}] {주제요약} · {YYMMDD}
```

- **플랫폼**: LinkedIn / Instagram / YouTube …(표 1의 사람이 읽는 이름)
- **위치**: 댓글 / 본문 / 바이오 / 영상설명 … (한글, 표 2 대응)
- **주제요약**: 도착지 콘텐츠 핵심을 **한글 6~14자**로. (페이지 제목/슬러그에서 압축, 회사명·접미사 제거)
- **YYMMDD**: 생성일.

예시:
- `[LinkedIn·댓글] 해커톤 교육 · 260601`
- `[YouTube·영상설명] 이랜드 AX교육 · 260601`
- `[Instagram·바이오] AX 빌더스 · 260601`

규칙:
- 40자 이내 권장. 회사명("조코딩 AX 파트너스 블로그") 같은 공통 꼬리표는 **빼서** 변별력 확보.
- 같은 콘텐츠를 여러 곳에 뿌리면 앞부분(플랫폼·위치)만 달라지고 주제요약은 동일 → 목록에서 세트로 보인다.

## 6. Back-half (custom keyword)

- **매번 사용자에게 물어본다.** (월 100개 한도 소모)
- 쓸 경우 추천 포맷: `{campaign}-{플랫폼약자}` (예: `hackathon-li`, `eland-yt`). 영소문자·하이픈.
- 생략하면 Bitly 랜덤 코드.
- ⚠️ **API 동작 주의**: `/custom_bitlinks`는 '랜덤 hash(부모) + 브랜드 별칭(자식)' 2개를 만들고
  별칭은 untitled로 생성된다. `bitly.py`가 자동으로 (1) 별칭에 제목·태그 이관 (2) 부모 hash를 archive
  처리해 목록을 1줄로 정리한다. archive 후에도 별칭 리다이렉트는 정상(검증 완료). Bitly엔 삭제 API가
  없어 archive로 숨김 처리하는 것이 정석.

## 7. Tags / QR

- **둘 다 수동(기본 off).** 사용자가 명시적으로 요청할 때만 `--tags` 부여 / QR 생성.

---

## 8. 도착지 주제 파악 절차

1. WebFetch로 도착지 URL의 `<title>`/h1 추출 → 주제요약 압축.
2. `blog.jocodingax.ai`는 봇 차단될 수 있음(브라우저 UA 필요). 실패 시:
   - URL 슬러그에서 추론 (`hackathon-edu` → "해커톤 교육"), 또는
   - 사용자에게 "이 링크 주제 한 줄?" 질문.
