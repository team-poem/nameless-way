# tao-counsel

도덕경 81장 전문을 근거 데이터로 두고, 현자 해석 중심 상담 세션을 돌리는
Claude Code 하네스.

Part of the Sobaya workspace — workspace conventions (brain,
orchestration, one-writer-per-app) live in the root CLAUDE.md and apply
here.

## App facts
- Stack: markdown 데이터 + Claude Code 스킬 (실행 코드 최소)
- Run: 이 디렉터리에서 Claude Code 세션을 열고 `Skill(counsel)` 호출
- Test: `tests/` 의 인용 검증 스크립트 (원문 대조) — 미구현

## Design decisions
- **원문 보유:** `text/` 에 81장 원문(한문)·한국어 번역을 장별 파일로 둔다.
  상담 중 인용은 반드시 이 파일에서 읽어온 문장만 사용 — 기억에서 짓지 않는다.
- **상담 스타일:** 해석 중심. 고민을 듣고 관련 장을 골라 해석해주고
  실천 제안까지. 소크라테스식 되묻기는 보조 수단.
- **기록:** 세션은 `sessions/` 에 날짜별 마크다운으로 남긴다.

## Orchestration
- Implementer: opus
