# tao-counsel

도덕경 81장 전문을 근거 데이터로 두고, 현자 해석 중심 상담 세션을 돌리는
Claude Code 하네스.

Part of the Sobaya workspace — workspace conventions (brain,
orchestration, one-writer-per-app) live in the root CLAUDE.md and apply
here.

## App facts
- Stack: markdown 데이터 + Claude Code 스킬 (실행 코드는 도구·테스트뿐,
  파이썬 표준 라이브러리만 씀)
- Run: 이 디렉터리에서 Claude Code 세션을 열고 `Skill(counsel)` 호출
- Test: `python3 tests/verify.py` — T1 인용 대조(필수) · T2 데이터 완결성
- Import: `python3 tools/import_wikisource.py --fetch` — 저본 재반입 (멱등)
- 라이선스: CC BY-SA 4.0 (저본이 BY-SA라 copyleft가 따라온다)

## Design decisions
- **원문 보유:** `text/NN.md` 에 장별로 네 섹션 — `원문`(한문) · `번역`(저본)
  · `현대어`(우리가 쓴 구어체 다리) · `주해`(해석 재료, 사용자에게 안 보임).
- **인용은 파일에서만:** 상담 인용은 반드시 Read 한 `원문`/`번역` 문장.
  기억에서 짓지 않는다. `tests/verify.py` T1 이 문자 단위로 대조한다.
- **저본은 못 고친다:** 오탈자·오역도 그대로 둔다. 고치면 T1 대조가 무너진다.
  바로잡을 것은 `주해`에 쓰거나 위키문헌에 기여한다.
- **오독 주의:** 모든 장 `주해` 마지막에 "이 장을 누구에게 쓰면 해가 되는지"가
  있다. 상담 중 이 항목에 걸리면 그 장을 버린다. T2 가 존재를 강제한다.
- **상담 스타일:** 해석 중심. 고민을 듣고 관련 장을 골라 해석해주고
  실천 제안까지. 소크라테스식 되묻기는 보조 수단.
- **기록:** 세션은 `sessions/` 에 날짜별 마크다운. 개인 기록이라 gitignore
  하고, 형식 예시만 `sessions/examples/` 에 추적한다.

## 설계 문서
`SPEC.md` 가 근거 문서다. 데이터 형식·스킬 단계·테스트·열린 항목이 거기 있다.

## Orchestration
- Implementer: opus
