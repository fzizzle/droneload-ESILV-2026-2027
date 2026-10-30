# docs/agent-rules

**Agent:** Claude Code (Opus 5.5)
**Status:** ready for review

## Goal
Set shared rules for quality, branches and logs, at low agent usage for contributors on free plans.

## Steps
- 2026-10-30: Added `AGENTS.md`, `CLAUDE.md`, `logs/` and README sections. Cut `AGENTS.md` after adding tooling.
- 2026-10-30: Added `check.sh`, `test_main.py`, `benchmark.py`, `ruff.toml`, CI and `requirements-dev.txt`.
- 2026-10-30: Fixed shellcheck warnings in `setup.sh` and `build_opencv.sh`, and an unused import.
- 2026-10-30: Added `docs/contest-rules.md`, summarised from the team's notes. Left out the team name and registration number.

## Verification
- `./check.sh` passed, with OpenCV 4.10.0 on Python 3.14. `benchmark.py` gave found=56.4% unmatched=26.6%.
- Not tested: the CI workflow, which needs a push, and whether other agent tools read `AGENTS.md`.

## Next Steps
- Push, confirm CI passes, then protect `main`. Record owners.
