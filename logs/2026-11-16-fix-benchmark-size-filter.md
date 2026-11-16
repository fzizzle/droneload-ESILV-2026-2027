# fix/benchmark-size-filter

**Agent:** Claude Code (Claude Sonnet)
**Status:** ready for review

## Goal
The benchmark ignored MIN_SIDE_PX, so it scored detections the app discards. Use the shared filter.

## Steps
- 2026-11-16: Old baseline: found=56.4% unmatched=26.6%; --track found=53.2% unmatched=2.4%.
- 2026-11-16: score() now calls vibration_test.find_markers. New: found=56.4% unmatched=10.9%; --track found=53.3% unmatched=1.4%.

## Decisions
- Reuse find_markers instead of repeating the filter.

## Verification
- `./scripts/check.sh`: all four [OK]. New test failed before (6 != 0), passes after.

## Next Steps
- Later detection changes compare with the new baseline.
