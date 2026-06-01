#!/usr/bin/env python3
"""
bitly.py — 조코딩ax Bitly 링크 단축 + UTM 자동화 (stdlib only)

서브커맨드:
  create  단축 링크 생성 (UTM 자동 결합 + 제목 + 선택적 custom back-half/tags)
  list    그룹의 전체 링크를 md 표로 출력 (= 전사 사용 히스토리/감사)

토큰/그룹은 config.env 또는 환경변수(BITLY_TOKEN, BITLY_GROUP_GUID)에서 읽음.
"""
import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
import urllib.error

API = "https://api-ssl.bitly.com/v4"
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(os.path.dirname(HERE), "config.env")


def load_config():
    cfg = {}
    if os.path.exists(CONFIG):
        with open(CONFIG) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                cfg[k.strip()] = v.strip().strip('"').strip("'")
    token = os.environ.get("BITLY_TOKEN") or cfg.get("BITLY_TOKEN")
    guid = os.environ.get("BITLY_GROUP_GUID") or cfg.get("BITLY_GROUP_GUID")
    if not token:
        sys.exit("ERROR: BITLY_TOKEN 없음 (config.env 또는 환경변수 설정 필요)")
    return token, guid


def api(method, path, token, body=None):
    url = API + path
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode()
        raise SystemExit(f"Bitly API {e.code} on {method} {path}: {detail}")


def build_long_url(url, source, medium, campaign, content, term):
    parts = urllib.parse.urlsplit(url)
    q = dict(urllib.parse.parse_qsl(parts.query, keep_blank_values=True))
    for k, v in [
        ("utm_source", source), ("utm_medium", medium), ("utm_campaign", campaign),
        ("utm_content", content), ("utm_term", term),
    ]:
        if v:
            q[k] = v
    new_q = urllib.parse.urlencode(q)
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path, new_q, parts.fragment))


def cmd_create(args):
    token, guid = load_config()
    long_url = build_long_url(args.url, args.source, args.medium, args.campaign, args.content, args.term)
    body = {"long_url": long_url, "domain": "bit.ly"}
    if guid:
        body["group_guid"] = guid
    if args.title:
        body["title"] = args.title
    if args.tags:
        body["tags"] = [t.strip() for t in args.tags.split(",") if t.strip()]
    res = api("POST", "/bitlinks", token, body)
    link = res["link"]
    bitlink_id = res["id"]

    # 선택적 custom back-half
    # 주의: /custom_bitlinks는 '부모(랜덤 hash) + 자식(브랜드 별칭)' 구조를 만든다.
    # 별칭은 untitled로 생성되고 부모 hash가 목록에 그대로 남아 링크가 2개로 보인다.
    # → 별칭에 제목을 이관하고, 부모 hash는 archive해서 목록에서 숨긴다(삭제 API 없음).
    #   archive 후에도 별칭 리다이렉트는 정상 동작함(검증 완료).
    warn = None
    if args.back_half:
        kw = args.back_half.lstrip("/")
        custom_id = "bit.ly/" + kw
        try:
            api("POST", "/custom_bitlinks", token, {
                "bitlink_id": bitlink_id,
                "custom_bitlink": custom_id,
            })
            if args.title:
                api("PATCH", "/bitlinks/" + custom_id, token, {"title": args.title})
            if args.tags:
                api("PATCH", "/bitlinks/" + custom_id, token,
                    {"tags": [t.strip() for t in args.tags.split(",") if t.strip()]})
            api("PATCH", "/bitlinks/" + bitlink_id, token, {"archived": True})
            link = "https://" + custom_id
            bitlink_id = custom_id
        except SystemExit as e:
            warn = f"custom back-half '{kw}' 실패 → 랜덤 링크 유지 ({e})"

    out = {"link": link, "title": res.get("title"), "long_url": long_url, "id": bitlink_id}
    if warn:
        out["warn"] = warn
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_list(args):
    token, guid = load_config()
    if not guid:
        sys.exit("ERROR: BITLY_GROUP_GUID 필요 (list 모드)")
    links = []
    page = f"/groups/{guid}/bitlinks?size={args.size}"
    while page:
        d = api("GET", page, token)
        links.extend(d.get("links", []))
        nxt = d.get("pagination", {}).get("next")
        if nxt and len(links) < args.max:
            page = nxt.replace(API, "")
        else:
            page = None

    rows = []
    for b in links[: args.max]:
        lu = b.get("long_url", "")
        q = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(lu).query))
        rows.append({
            "date": (b.get("created_at", "")[:10]),
            "link": b.get("id", ""),
            "title": (b.get("title") or "").replace("|", "/"),
            "src": q.get("utm_source", ""),
            "med": q.get("utm_medium", ""),
            "camp": q.get("utm_campaign", ""),
            "content": q.get("utm_content", ""),
            "dest": urllib.parse.urlsplit(lu).netloc + urllib.parse.urlsplit(lu).path,
        })

    md = ["# Bitly 링크 히스토리 (group: %s)" % guid, "",
          "| 날짜 | 단축링크 | 제목 | source | medium | campaign | content | 도착지 |",
          "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append("| {date} | {link} | {title} | {src} | {med} | {camp} | {content} | {dest} |".format(**r))
    md.append("")
    md.append(f"_총 {len(rows)}건_")
    text = "\n".join(md)
    if args.out:
        with open(args.out, "w") as f:
            f.write(text + "\n")
        print(f"wrote {len(rows)} links -> {args.out}")
    else:
        print(text)


def main():
    p = argparse.ArgumentParser(description="Bitly 링크 단축 + UTM 자동화")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create")
    c.add_argument("--url", required=True, help="원본 도착지 URL")
    c.add_argument("--source", required=True)
    c.add_argument("--medium", required=True)
    c.add_argument("--campaign", required=True)
    c.add_argument("--content", default="")
    c.add_argument("--term", default="")
    c.add_argument("--title", required=True)
    c.add_argument("--back-half", default="", help="custom keyword (생략 시 랜덤)")
    c.add_argument("--tags", default="")
    c.set_defaults(func=cmd_create)

    l = sub.add_parser("list")
    l.add_argument("--size", type=int, default=50)
    l.add_argument("--max", type=int, default=200)
    l.add_argument("--out", default="", help="md 파일 경로 (생략 시 stdout)")
    l.set_defaults(func=cmd_list)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
