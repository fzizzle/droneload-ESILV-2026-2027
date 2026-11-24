# docs/f450-build-guide

**Agent:** Claude Code (Claude Opus 5.5)
**Status:** ready for review

## Goal
Add an English and French build guide for the F450 loan kit, rewritten from the team's printed Hawk's Work quick start book.

## Steps
- 2026-11-24: Rebuilt the booklet (pp. 1, 3–15) as a 20-page guide per language, following its six parts with every step, note and figure.
- 2026-11-24: Figures come from the online edition of the same guide; six LCD screens were AI-upscaled (Gemini) and checked against the originals. A Gemini Mission Planner screenshot that changed a label was rejected.
- 2026-11-24: An independent check against the booklet photos found no wrong facts; fixed one dropped word ("left pins"), page refs and captions.
- 2026-11-24: Compressed both PDFs from 6.3 MB to 4.0 MB with Ghostscript; links and fonts kept.

## Decisions
- PDFs committed as an exception to the generated-files and English-only rules (see DECISIONS.md).

## Verification
- `./scripts/check.sh`: shell syntax, shellcheck, ruff and pytest all OK. All 10 links in each PDF return 200. Hardware steps are not tested on the kit.

## Next Steps
- Upscale the remaining 13 screenshots when the Gemini quota resets, if wanted.
