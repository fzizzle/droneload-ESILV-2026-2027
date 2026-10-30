# Agent Rules

Rules for every agent and contributor. This file loads into each agent session, so keep it short.

## Project Context

- ArUco marker detection for the Droneload 2027 contest (ESILV PI2). The output is logged pixel positions only.
- Automatic flight earns most flight points (670 of 1,320 total), and 2027 rules are provisional. Open `docs/contest-rules.md` only for contest questions.
- Assume the organisers' loan kit: F450 frame, Pixhawk 2, PMW3901 optical flow and Marvelmind beacons. The companion computer and cameras are not chosen, so keep camera code hardware-independent.
- Owners: not recorded yet. Ask the project lead.

## Keep Usage Low

Some contributors use free plans.

- Read only what the task needs: `TODO.md`, `logs/DECISIONS.md` and your branch's log. Open the README, other logs or other files only when required.
- Never open `test_footage/`, images or videos unless the task needs it.
- Run `./scripts/check.sh` instead of separate commands. Its output is short.
- Do not paste long output into logs or pull requests. Summarise it.
- Use the benchmark only for detection changes.
- Work in one module at a time.

## Workflow

1. Create a branch: `<type>/<short-description>`, with type `feature`, `fix`, `docs`, `test` or `chore`. Never commit directly to `main`.
2. Create `logs/YYYY-MM-DD-<branch-name>.md` from `logs/TEMPLATE.md`, replacing `/` with `-`. Keep it to 20 lines and update it as you work.
3. Keep the branch to one purpose. Put unrelated problems in `TODO.md`.
4. Add lasting decisions to `logs/DECISIONS.md`, one line each.
5. Commit to your branch as you work, without waiting to be asked. When finished, push it and open a pull request saying what changed, how it was verified and what remains.

Push only to `origin`. Never force-push shared branches or edit another agent's log entries.

## Stop and Ask

Get a person's decision before you:

- choose or assume hardware beyond the loan kit
- change marker IDs, labels, the default dictionary or the CSV format
- add a dependency
- push to `upstream` (`YUu-8/Droneload`, the previous team's repository)
- write code that commands a drone or talks to a flight controller

## Code

- Match the surrounding code. Do not refactor unrelated code.
- Use the standard library and standard packages before custom code.
- Follow the module boundaries in `docs/architecture.md`.
- Camera code goes in `droneload/vision/camera_*.py`, with `open()`, `read()` and `release()`.
- Settings go in constants at the top of each module's main file.
- `scripts/test_camera.sh` and `camera_rubikpi_csi.py` must use the same pipeline.
- Add a test in `tests/` for each new behaviour or bug fix.
- Delete dead code instead of commenting it out.

## Repository

- Never commit generated files or footage. Stage files by name.
- Use UTF-8 and LF.
- `README.md` and `README.fr.md` must stay in step. Other docs are in English only.

## Verification

Set up with the README, then before review:

```bash
./scripts/check.sh
```

For detection changes, also run `python -m testing.benchmark` before and after, and log both results. The baseline is `found=56.4% unmatched=26.6%`. The footage is listed in the README. Passing the generated test video does not show detection quality is good.

## Reporting

- Report what happened, including failures and skipped checks.
- Camera and board behaviour count as tested only when run on that hardware.
- Mark unchecked hardware or package claims as unverified.

## Done Means

- [ ] `./scripts/check.sh` passes
- [ ] Log, `TODO.md` and both READMEs are up to date
- [ ] Pull request is open
