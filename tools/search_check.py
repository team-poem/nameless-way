#!/usr/bin/env python3
"""검색 품질 점검 — 고민 문장을 넣으면 어떤 장이 걸리는지 본다.

상담 스킬 3단계(검색)가 실제로 되는지 사람이 눈으로 확인하기 위한 도구다.
테스트가 아니라 점검용이라 통과/실패를 매기지 않는다.

    python3 tools/search_check.py "팀장이 자꾸 내 일에 끼어들어서 미치겠어"
    python3 tools/search_check.py --stats

점수는 단순 어절 겹침이다. 임베딩을 쓰지 않는 이유는 SPEC §3 참조 —
`situations` 가 고민의 언어로 쓰여 있으면 이 정도로 충분한지가 확인 대상.
"""

import argparse
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT = ROOT / "text"

# 조사·어미가 붙어도 걸리도록 어절 앞부분만 본다
STOP = {"때", "것", "거", "게", "수", "안", "못", "더", "좀", "왜", "나", "내", "그"}


def tokens(s):
    out = set()
    for w in re.findall(r"[가-힣A-Za-z]+", s):
        if len(w) < 2 or w in STOP:
            continue
        out.add(w)
        if len(w) > 2:
            out.add(w[:2])   # 조사 제거 근사
        if len(w) > 3:
            out.add(w[:3])
    return out


def load():
    chapters = []
    for p in sorted(TEXT.glob("[0-9]*.md")):
        s = p.read_text(encoding="utf-8")
        fm = s.split("---")[1] if s.startswith("---") else ""
        n = int(re.search(r"^chapter:\s*(\d+)", fm, re.M).group(1))
        themes = re.search(r"^themes:\s*\[(.*)\]", fm, re.M)
        themes = [t.strip() for t in themes.group(1).split(",")] if themes else []
        sits = [x.strip() for x in re.findall(r"^\s+-\s+(.+)$", fm, re.M)]
        chapters.append((n, themes, sits))
    return chapters


def search(worry, chapters, top=6):
    q = tokens(worry)
    scored = []
    for n, themes, sits in chapters:
        best, hit = 0, ""
        for s in sits:
            overlap = len(q & tokens(s))
            if overlap > best:
                best, hit = overlap, s
        theme_hit = len(q & tokens(" ".join(themes)))
        score = best * 2 + theme_hit
        if score:
            scored.append((score, n, hit or ", ".join(themes)))
    scored.sort(reverse=True)
    return scored[:top]


def stats(chapters):
    all_sits = [s for _, _, sits in chapters for s in sits]
    print(f"장 {len(chapters)} · situations {len(all_sits)} · 고유 {len(set(all_sits))}")

    # 어떤 낱말이 상황 문장에 몰려 있는가 — 한 축에 장이 쏠리는지 본다
    counter = collections.Counter()
    for _, _, sits in chapters:
        seen = set()
        for s in sits:
            for w in re.findall(r"[가-힣]{2,}", s):
                if w not in STOP:
                    seen.add(w)
        counter.update(seen)
    print("\n가장 많은 장에 걸친 낱말 (몰림 확인):")
    for w, c in counter.most_common(12):
        print(f"  {c:2d}장 — {w}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("worry", nargs="*", help="고민 문장")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    chapters = load()
    if args.stats:
        stats(chapters)
        return 0
    if not args.worry:
        ap.error("고민 문장을 넣거나 --stats 를 쓸 것")

    worry = " ".join(args.worry)
    print(f"고민: {worry}\n")
    hits = search(worry, chapters)
    if not hits:
        print("  걸리는 장 없음")
        return 0
    for score, n, why in hits:
        print(f"  {score:3d}점  {n:2d}장  ← {why}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
