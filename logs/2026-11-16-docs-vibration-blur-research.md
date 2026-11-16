# docs/vibration-blur-research

**Agent:** Claude Code, Claude Opus 5.5
**Status:** ready for review

## Goal
Research how to improve marker detection on footage hit by vibration and motion blur, and save a report.

## Steps
- 2026-11-16: Researched camera hardware and mounting, image restoration, detector robustness and temporal tracking from web sources. Wrote `docs/research/vibration-and-blur.md` with a ranked list of 13 things to try.
- 2026-11-16: Checked the main code claim: with one bit flipped on a `DICT_4X4_50` marker, OpenCV 4.10 rejects it at `errorCorrectionRate` 0.6 and 0.99, and detects it at 1.0.
- 2026-11-16: Added the four sourced research notes in `docs/research/vibration-and-blur-notes/`.

## Decisions
- None. The report lists the items that need a person's decision.

## Verification
- `./scripts/check.sh` passes (shell syntax, shellcheck, ruff, pytest). No code changed, so the benchmark and vibration test were not run. Hardware, Qualcomm and price claims are unverified.

## Next Steps
- Try items 1-3 of the report's table (gate sweep, raw logged positions, drop IDs outside 0-9).
