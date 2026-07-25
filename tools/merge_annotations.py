#!/usr/bin/env python3
"""주석 조각을 text/NN.md 에 합친다.

서브에이전트는 저장소를 건드리지 않고 조각 파일만 쓴다(한 앱에 쓰는 사람은
하나). 이 스크립트가 조각을 읽어 `themes`/`situations`/`현대어`/`주해` 만
갈아끼운다. `원문`/`번역` 은 절대 건드리지 않는다.

    python3 tools/merge_annotations.py <조각디렉터리>

조각 파일 이름은 `NN.part.md`, 형식은:

    themes: [물, 다투지 않음]
    situations:
      - 경쟁이 버거울 때
      - 애써도 공을 못 받을 때
    %%현대어%%
    ...
    %%주해%%
    ...
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TEXT = ROOT / "text"
SECTIONS = ("원문", "번역", "현대어", "주해")


def parse_part(text):
    m = re.search(r"%%현대어%%\n(.*?)\n%%주해%%\n(.*)", text, re.S)
    if not m:
        raise ValueError("%%현대어%% / %%주해%% 표시를 찾을 수 없다")
    head = text[: m.start()]
    modern, note = m.group(1).strip(), m.group(2).strip()

    themes = re.search(r"^themes:\s*(.+)$", head, re.M)
    if not themes:
        raise ValueError("themes 줄이 없다")
    sits = re.findall(r"^\s*-\s*(.+)$", head, re.M)
    if not sits:
        raise ValueError("situations 항목이 없다")
    if not modern or not note:
        raise ValueError("현대어 또는 주해가 비었다")
    if "오독 주의" not in note:
        raise ValueError("주해에 '오독 주의' 가 없다")
    return themes.group(1).strip(), sits, modern, note


def split_sections(md):
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


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    src = pathlib.Path(sys.argv[1])
    parts = sorted(src.glob("*.part.md"))
    if not parts:
        print(f"조각이 없다: {src}", file=sys.stderr)
        return 1

    ok = 0
    errors = []
    for part in parts:
        n = int(part.name.split(".")[0])
        target = TEXT / f"{n:02d}.md"
        if not target.exists():
            errors.append(f"{n:02d}: 대상 파일 없음")
            continue
        try:
            themes, sits, modern, note = parse_part(part.read_text(encoding="utf-8"))
        except ValueError as e:
            errors.append(f"{n:02d}: {e}")
            continue

        fm, secs = split_sections(target.read_text(encoding="utf-8"))
        sit_block = "\n".join(f"  - {s}" for s in sits)
        fm = (
            "---\n"
            f"chapter: {n}\n"
            f"themes: {themes}\n"
            f"situations:\n{sit_block}\n"
            "source: wikisource-ko\n"
            "---\n"
        )
        secs["현대어"] = modern
        secs["주해"] = note
        body = "\n\n".join(f"## {k}\n\n{secs.get(k, '').strip()}" for k in SECTIONS)
        target.write_text(f"{fm}\n{body}\n", encoding="utf-8")
        ok += 1

    print(f"합침 {ok} · 실패 {len(errors)}")
    for e in errors:
        print(f"  ! {e}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
