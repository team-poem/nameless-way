#!/usr/bin/env python3
"""위키문헌 「번역:도덕경」 원본 위키텍스트를 text/NN.md 로 옮긴다.

의존성 없음. 멱등 — 이미 있는 파일의 `현대어`/`주해`/프론트매터는 보존하고
`원문`/`번역` 섹션만 저본으로 다시 맞춘다.

    python3 tools/import_wikisource.py --fetch
    python3 tools/import_wikisource.py --from ddj.wiki

저본: https://ko.wikisource.org/wiki/번역:도덕경  (CC BY-SA 3.0 / GFDL 1.2)
자세한 것은 text/SOURCE.md.
"""

import argparse
import pathlib
import re
import sys
import urllib.request

RAW_URL = (
    "https://ko.wikisource.org/w/index.php"
    "?title=%EB%B2%88%EC%97%AD:%EB%8F%84%EB%8D%95%EA%B2%BD&action=raw"
)
UA = "tao-counsel/0.1 (https://github.com/team-poem/nameless-way)"

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT = ROOT / "text"

# 저본에는 `=== 제60장  ===` 처럼 공백이 더 붙은 제목이 섞여 있다.
CHAPTER_RE = re.compile(r"^===\s*제(\d+)장\s*===\s*$", re.M)
POEM_RE = re.compile(r"<poem>(.*?)</poem>", re.S)
COMMENT_RE = re.compile(r"<!--.*?-->", re.S)
# 53장만 <poem> 대신 {{번역 표|...|...}} 안에 <br> 로 줄을 나눈다.
TABLE_RE = re.compile(r"\{\{번역 표\s*(.*?)\}\}", re.S)
REF_RE = re.compile(r"<ref[^>]*/>|<ref[^>]*>.*?</ref>", re.S)
BR_RE = re.compile(r"<br\s*/?>", re.I)

SECTIONS = ("원문", "번역", "현대어", "주해")

NEW_FRONTMATTER = """---
chapter: {n}
themes: []
situations: []
source: wikisource-ko
---
"""


def fetch() -> str:
    req = urllib.request.Request(RAW_URL, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8")


def clean(poem: str) -> str:
    """위키 편집자 주석과 각주만 걷어낸다. 본문은 오탈자까지 그대로 둔다."""
    poem = COMMENT_RE.sub("", poem)
    poem = REF_RE.sub("", poem)
    lines = [ln.rstrip() for ln in poem.split("\n")]
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return "\n".join(lines)


def extract(block):
    """한 장의 위키텍스트에서 (번역, 원문) 을 뽑는다. 못 뽑으면 None."""
    poems = POEM_RE.findall(block)
    if len(poems) >= 2:
        return clean(poems[0]), clean(poems[1])

    # <poem> 이 없는 장 — {{번역 표}} 의 두 인자를 <br> 기준으로 가른다
    table = TABLE_RE.search(block)
    if not table:
        return None
    body = REF_RE.sub("", table.group(1))
    args = [a for a in body.split("\n|") if a.strip()]
    if len(args) < 2:
        args = [a for a in body.split("|") if a.strip()]
    if len(args) < 2:
        return None
    def tidy(a):
        a = BR_RE.sub("\n", a).lstrip("|")
        lines = [ln.strip() for ln in a.split("\n")]
        return "\n".join(ln for ln in lines if ln)  # <br> 로 생긴 빈 줄을 접는다

    return tidy(args[0]), tidy(args[1])


def parse(wikitext):
    """{장번호: (번역, 원문)}"""
    out = {}
    marks = list(CHAPTER_RE.finditer(wikitext))
    for i, m in enumerate(marks):
        n = int(m.group(1))
        end = marks[i + 1].start() if i + 1 < len(marks) else len(wikitext)
        got = extract(wikitext[m.end():end])
        if got is None:
            print(f"  ! 제{n}장 — 번역/원문을 못 찾음, 건너뜀", file=sys.stderr)
            continue
        out[n] = got
    return out


def split_sections(md):
    """기존 파일을 (프론트매터, {섹션: 본문}) 으로 가른다."""
    fm = ""
    if md.startswith("---\n"):
        end = md.find("\n---\n", 4)
        if end != -1:
            fm, md = md[: end + 5], md[end + 5:]
    secs = {}
    parts = re.split(r"^## (.+)$", md, flags=re.M)
    for i in range(1, len(parts), 2):
        secs[parts[i].strip()] = parts[i + 1].strip("\n")
    return fm, secs


def render(fm, secs):
    body = "\n\n".join(f"## {k}\n\n{secs.get(k, '').strip()}" for k in SECTIONS)
    return f"{fm}\n{body}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fetch", action="store_true", help="위키문헌에서 직접 받는다")
    ap.add_argument("--from", dest="src", help="받아둔 위키텍스트 파일")
    args = ap.parse_args()

    if args.fetch:
        wikitext = fetch()
    elif args.src:
        wikitext = pathlib.Path(args.src).read_text(encoding="utf-8")
    else:
        ap.error("--fetch 또는 --from 중 하나가 필요하다")

    chapters = parse(wikitext)
    print(f"{len(chapters)}개 장을 읽었다")
    if len(chapters) != 81:
        print(f"  ! 81장이 아니다 ({len(chapters)}장). 저본이 바뀌었는지 확인할 것.",
              file=sys.stderr)

    TEXT.mkdir(exist_ok=True)
    created = updated = unchanged = 0
    for n in sorted(chapters):
        trans, orig = chapters[n]
        path = TEXT / f"{n:02d}.md"

        before = path.read_text(encoding="utf-8") if path.exists() else None
        fm, secs = split_sections(before) if before else (NEW_FRONTMATTER.format(n=n), {})

        secs["원문"] = orig
        secs["번역"] = trans
        secs.setdefault("현대어", "")
        secs.setdefault("주해", "")
        after = render(fm, secs)

        if before is None:
            created += 1
        elif before != after:
            updated += 1
        else:
            unchanged += 1
        path.write_text(after, encoding="utf-8")

    print(f"새로 만듦 {created} · 갱신 {updated} · 그대로 {unchanged}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
