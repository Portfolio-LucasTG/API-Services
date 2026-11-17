---
description: Implement the next unchecked step of docs/PLAN.md (or the step number given)
argument-hint: "[step number]"
---

Implement one step of the plan.

1. Read `CLAUDE.md`, `docs/PLAN.md` and the `CLAUDE.md` of every service the step touches.
2. Pick the step: if `$ARGUMENTS` is a number, use that step; otherwise the first step with an unticked box.
   If an earlier step is still unticked, stop and tell me.
3. Before writing code, list in 3–6 bullets what you will create or change and which tests you will write.
4. Implement the step **with its tests**. Stay inside the step's scope.
5. Run `make check` plus the step's "Done when" commands. Fix everything until they pass.
   Never weaken lint/type/coverage settings to get green.
6. Tick the step's boxes in `docs/PLAN.md`.
7. Finish with: files changed, test count/coverage, anything I must do by hand,
   and a suggested Conventional Commit message. Do not commit unless I ask.
