# fix/polygon-accuracy

**Agent:** Claude Code (Claude Sonnet)
**Status:** ready for review
## Goal
Return `polygonalApproxAccuracyRate` to OpenCV's default 0.03 (was 0.05), a detection change.

## Steps
- 2026-11-16: Before: benchmark found=56.4% unmatched=10.9%; `--track` 53.3% / 1.4%; moderate raw=63.8% tracked=54.1% (err 1.7 px), severe raw 3.9%.
- 2026-11-16: Removed the setting; bumped `CACHE_VERSION` to 3; added a test (failed 0.05 != 0.03, then passed).
- 2026-11-16: After: benchmark 57.6% / 4.1%; `--track` 54.8% / 0.8%; moderate raw=65.9% tracked=57.2% (err 1.7 px), severe raw 2.4%.

## Decisions
- Default 0.03 wins on every headline number; severe shake got slightly worse (raw 3.9% to 2.4%).
- Neither footage uses `DICT_4X4_50`, so this is unconfirmed for the contest dictionary.
## Verification
- `./scripts/check.sh` passes. No hardware tested.

## Next Steps
- Re-check on real `DICT_4X4_50` flight footage.
