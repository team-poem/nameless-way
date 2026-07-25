#!/usr/bin/env python3
"""tao-counsel 검증 — T1 인용 대조, T2 데이터 완결성.

의존성 없음.

    python3 tests/verify.py            # 둘 다
    python3 tests/verify.py --only t1

T1 이 이 프로젝트의 유일한 필수 테스트다. 상담에서 나간 도덕경 인용이
정말 `text/` 파일에 있는 문장인지 문자 단위로 대조한다. 이게 통과하지
않으면 "근거 있는 인용"이라는 이 프로젝트의 존재 이유가 무너진다.
"""

import argparse
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT = ROOT / "text"
SESSIONS = ROOT / "sessions"

SECTIONS = ("원문", "번역", "현대어", "주해")
QUOTABLE = ("원문", "번역")          # 인용해도 되는 섹션
FRONTMATTER_FIELDS = ("chapter", "themes", "situations", "source")

# 세션 기록의 인용 머리표 — [8장 번역]
MARKER_RE = re.compile(r"^\[(\d+)장\s+(\S+)\]\s*$", re.M)


def load_chapter(n):
    """{섹션: [줄]} — 없으면 None"""
    path = TEXT / f"{n:02d}.md"
    if not path.exists():
        return None
    md = path.read_text(encoding="utf-8")
    if md.startswith("---\n"):
        end = md.find("\n---\n", 4)
        if end != -1:
            md = md[end + 5:]
    secs = {}
    parts = re.split(r"^## (.+)$", md, flags=re.M)
    for i in range(1, len(parts), 2):
        body = parts[i + 1]
        secs[parts[i].strip()] = [ln.strip() for ln in body.split("\n") if ln.strip()]
    return secs


def t1_quotes():
    """세션 기록의 인용이 원본과 일치하는가."""
    fails = []
    checked = 0
    files = sorted(SESSIONS.rglob("*.md")) if SESSIONS.exists() else []

    for f in files:
        rel = f.relative_to(ROOT)
        text = f.read_text(encoding="utf-8")
        marks = list(MARKER_RE.finditer(text))
        for i, m in enumerate(marks):
            n, section = int(m.group(1)), m.group(2)
            line_no = text[: m.start()].count("\n") + 1

            if section not in QUOTABLE:
                fails.append(
                    f"{rel}:{line_no} — [{n}장 {section}] 은 인용할 수 없는 섹션. "
                    f"인용은 {'/'.join(QUOTABLE)} 만."
                )
                continue

            secs = load_chapter(n)
            if secs is None:
                fails.append(f"{rel}:{line_no} — {n}장 파일이 없다")
                continue
            haystack = set(secs.get(section, []))
            if not haystack:
                fails.append(f"{rel}:{line_no} — {n}장에 '{section}' 섹션이 비었다")
                continue

            # 머리표 다음 줄부터 빈 줄까지가 인용 블록
            end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
            # 머리표 자체의 줄바꿈은 건너뛴다 — 안 그러면 첫 줄에서 바로 끊긴다
            block = text[m.end():end].lstrip("\n")
            for raw in block.split("\n"):
                line = raw.strip()
                if not line:
                    break
                checked += 1
                if line not in haystack:
                    fails.append(f"{rel} — {n}장 {section}에 없는 문장: {line!r}")

    return checked, fails, len(files)


def t2_data():
    """81장 데이터가 온전한가."""
    fails = []
    for n in range(1, 82):
        path = TEXT / f"{n:02d}.md"
        if not path.exists():
            fails.append(f"{n:02d}.md 없음")
            continue
        md = path.read_text(encoding="utf-8")

        if not md.startswith("---\n"):
            fails.append(f"{n:02d}: 프론트매터 없음")
            continue
        end = md.find("\n---\n", 4)
        fm = md[4:end] if end != -1 else ""
        for field in FRONTMATTER_FIELDS:
            if not re.search(rf"^{field}:", fm, re.M):
                fails.append(f"{n:02d}: 프론트매터에 {field} 없음")

        if not re.search(r"^situations:\s*\n(\s+-\s+\S+)", fm, re.M):
            fails.append(f"{n:02d}: situations 가 비었다")

        secs = load_chapter(n) or {}
        for s in SECTIONS:
            if not secs.get(s):
                fails.append(f"{n:02d}: '{s}' 섹션이 비었다")

        note = "\n".join(secs.get("주해", []))
        if note and "오독 주의" not in note:
            fails.append(f"{n:02d}: 주해에 '오독 주의' 가 없다")

    return fails


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["t1", "t2"])
    args = ap.parse_args()

    failed = False

    if args.only != "t2":
        checked, fails, nfiles = t1_quotes()
        print(f"T1 인용 대조 — 세션 {nfiles}개, 인용 {checked}줄")
        if fails:
            failed = True
            for f in fails:
                print(f"  ✗ {f}")
        else:
            print("  ✓ 모든 인용이 원본과 일치")

    if args.only != "t1":
        fails = t2_data()
        print(f"T2 데이터 완결성 — 81장")
        if fails:
            failed = True
            for f in fails[:40]:
                print(f"  ✗ {f}")
            if len(fails) > 40:
                print(f"  … 외 {len(fails) - 40}건")
        else:
            print("  ✓ 81장 모두 온전")

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
