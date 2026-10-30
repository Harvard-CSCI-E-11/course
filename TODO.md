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

### January 2027 AWS readiness checklist

- [ ] Enable PITR for persistent DynamoDB tables (`e11-users` and `Leaderboard`)
  and verify the recovery window.
- [ ] Create DynamoDB backups and verify restoration into isolated temporary
  tables. Keep ephemeral sessions out of routine restores.
- [ ] Configure AWS Backup plans/vaults, schedules and retention; verify jobs and
  a restore.
- [ ] Enable `csci-e-11` S3 versioning; verify recovery using disposable test objects.

These are January tasks, not authorization to enable them now.

### Proposed Lambda security and reliability fixes

- Use host-only `__Host-` cookies. Expire the parent-domain cookie and require a
  new session-version marker so stolen old IDs cannot be replayed under the new
  name. Preserve separate session tables and intentionally shared course data.
- Enable Jinja HTML autoescaping and restore its HTML-safe `tojson` filter for
  values embedded in JavaScript. Test reflected errors, stored names and
  closing-script payloads.
- Log request IDs/actions/outcomes instead of events, auth payloads, cookies and
  token responses. Remove request-controlled log levels. Redact at the call sites.
  Keep production at INFO; full payload logging at that level still needs removal.
- Replace PEM-bearing errors with a fixed message and suppressed chaining. Return
  generic public errors with a request ID, not exception text or session IDs.
- Report retryable SQS exceptions and returned failures in `batchItemFailures`;
  quarantine invalid jobs. Add grade/email job idempotency and at least 362-second
  queue visibility. Retry definite SES quota rejections; never blindly retry
  submissions with uncertain acceptance.
- Bind OIDC transactions to a short-lived host-only browser cookie and an atomic,
  server-side transaction. Keep the PKCE verifier out of readable signed state.
- Route the actual scheduled heartbeat event to cleanup. Write DynamoDB `ttl`
  equal to `session_expire` on new sessions, preserving the existing table TTL
  configuration. Cleanup can remove legacy expired rows; keep read-time expiry checks.

These are proposals, not implementations in the uv/grading/log-retention change.
The published leaderboard signing key is deliberately retained for students to hack.

### Other course operations

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
