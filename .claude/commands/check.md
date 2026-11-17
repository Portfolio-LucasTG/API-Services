---
description: Run all code checks and fix what fails
---

Run `make check`. For every failure:

- ruff / eslint / prettier: run `make format`, then fix what remains by hand.
- mypy / vue-tsc: fix the types; `# type: ignore[code]` only with a reason comment.
- tests: find the root cause; fix the code if it breaks the contract in `api/CLAUDE.md`,
  fix the test only if the test is wrong (say which and why).
- coverage below 90 %: add meaningful tests for the uncovered branches.

Do not change tool configuration (`pyproject.toml` `[tool.*]`, `eslint.config.*`, `.prettierrc*`)
to make a check pass. Re-run `make check` until it is green and report the final summary.
