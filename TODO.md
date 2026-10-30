# Course backlog

Reviewed against the repository on 2026-08-23. Completed and superseded ideas
from the former scratch list were removed; the items below still need a decision
or implementation.

## Spring 2027 preparation deadlines

- [ ] Finish Labs 1–6 by **November 10, 2026**.
- [ ] Simson will upgrade Labs 7–8 by **December 1, 2026**. Their imported
  MEMENTO/CircuitPython guides remain legacy material until that work is complete;
  the Raspberry Pi upgrade is deferred from the current cleanup PR and is not
  assigned to Codex.

## Course operations

- Add a staff progress report that summarizes registration and started/completed
  counts per lab. `e11admin class`, `student-report`, `print-grades`, and `status`
  provide related views, but `status` currently reports grade increases since
  the last Canvas export rather than overall progress.
- Decide whether forced/batch grading should skip students who already have a
  winning or perfect result. The current `force-grade` workflow does not expose
  that policy.
- Decide whether the leaderboard needs a user-visible history view. Leaderboard
  events are recorded, but the current page presents active and inactive players
  rather than historical results.

## Lab installation and grading

- Finish the service and nginx installation targets for labs 4--6. Their
  `install-lab*-nginx` targets remain placeholders; service installation is
  present but duplicated across lab Makefiles. Include template substitution,
  `nginx -t`, reload, and certificate provisioning in the design.
- Complete the lab 1 attack/progress checks. The grader checks the retained
  journal, autograder key, and removal of the `hacker` account, but it does not
  identify the assigned attack or select registered students by current score.
- Audit the assignment writeups so that each one identifies the files students
  should modify and explains that linked shared files are not student-owned.
  The root README now documents the repository-level symlink design.
- Decide whether maintained reference-solution scripts and an automated
  end-to-end course rehearsal are desired. If so, define their security boundary
  and keep them out of student-facing installation paths.

Detailed `e11` testing and implementation debt is tracked separately in
[`etc/e11-cli/doc/TODO.md`](etc/e11-cli/doc/TODO.md).
