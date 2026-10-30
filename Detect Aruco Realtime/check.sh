#!/bin/bash
# check.sh - Run all checks. Prints one line per check, plus details on failure.

cd "$(dirname "$0")" || exit 1
fail=0

run() {
    name=$1
    shift
    if output=$("$@" 2>&1); then
        echo "[OK]   $name"
    else
        echo "[FAIL] $name"
        echo "$output" | tail -20
        fail=1
    fi
}

run "shell syntax" bash -c 'for s in *.sh; do bash -n "$s" || exit 1; done'
run "shellcheck"   shellcheck --severity=warning ./*.sh
run "ruff"         ruff check --quiet .
run "pytest"       python3 -m pytest -q --tb=short

exit $fail
