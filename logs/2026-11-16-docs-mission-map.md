# docs/mission-map

**Agent:** Claude Code, Claude Opus 5.5
**Status:** ready for review

## Goal
A shareable map of the mission: each goal in order, the functions it needs, their status, and the arena zones.

## Steps
- 2026-11-16: Added `docs/mission-map.md` (Mermaid flowchart, 8 steps, 54 functions, plus a table per step) and `docs/arena-map.svg`. Linked from both READMEs.
- 2026-11-16: Rendered the flowchart with mermaid-cli 11.4.2; routes needed explicit subgraph directions.

## Decisions
- Zone positions are a guess, as the rules summary has no field plan; `contest-rules.md` lists the question.

## Verification
- `./scripts/check.sh`: all four checks pass. Not checked: GitHub's own Mermaid rendering.

## Next Steps
- Replace the sketch when a field plan is published, and update statuses as functions are built.
