# docs/rules-v1

**Agent:** Claude Code, Claude Opus 5.5
**Status:** ready for review

## Goal
Update the contest summary and the agent rules from the V1 rules (15 Nov 2026).

## Steps
- 2026-11-17: Read all 32 pages of V1, figures included. Rewrote `docs/contest-rules.md`: dates, final, loan kit (annex 1), arena layout from Figure 1, objects, robot and open questions. Scoring is unchanged from V0.
- 2026-11-17: Decoded the annex 5 robot photos with OpenCV: ID 1 in `DICT_4X4_50`, matching the default.
- 2026-11-17: `AGENTS.md` kit line now names the MTF-01 and one Marvelmind beacon, with a lent Qualcomm computer and a possible second one. Updated V0 mentions in `TODO.md`, both READMEs and the stabilisation README.

## Decisions
- Project lead: a Qualcomm computer will be lent; the team may buy another for better camera compatibility.

## Verification
- `./scripts/check.sh`: shell syntax, shellcheck, ruff and pytest pass. Docs only; nothing run on hardware.

## Next Steps
- Redraw the arena map from Figure 1 (in `TODO.md`). Module READMEs still cite "2027 V0" for rules that V1 did not change.
