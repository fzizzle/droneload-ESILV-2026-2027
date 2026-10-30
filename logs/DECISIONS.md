# Decisions

Lasting decisions, one line each. Keep this file short.

- 2026-10-30: Hardware is undecided, so sources are chosen with `--source` through `cv2.VideoCapture`.
- 2026-10-30: `DICT_4X4_50` stays the default dictionary; `--dict` exists for test footage.
- 2026-10-30: `AGENTS.md` is the single rules file; `CLAUDE.md` only imports it.
- 2026-10-30: `ruff` lints but does not format, because `detect.py` uses aligned assignments.
- 2026-10-30: Rules are pinned in `ruff.toml` so every contributor gets the same result.
- 2026-10-30: Expensive checks run in CI, because CI costs agents no tokens.
- 2026-10-30: `ARUCO_LABELS` keeps the 2026 IDs until 2027 IDs are published.
- 2026-10-30: Code is organised by module; see `docs/architecture.md`.
- 2026-10-30: Install instructions use a `.venv` and the `python` command, which works on Mac, Windows and Linux.
- 2026-10-30: Only the main README has a French version. Other docs are in English, because a second language doubles each edit.
