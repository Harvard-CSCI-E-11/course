# Lambda Home

`lambda-home` is the AWS SAM application that serves the CSCI E-11 student dashboard, registration API, grading API, OIDC login flow, and upload callbacks.

## Layout

```text
lambda-home/
├── src/home_app/          # Lambda application package
├── src/e11/              # Generated runtime package installed from the e11 wheel
├── tests/                 # Lambda Home tests
├── template.yaml          # SAM template
├── samconfig-prod.toml
├── samconfig-stage.toml
└── Makefile               # Supported build, test, lint, and deploy workflow
```

## Workflow

Use the Makefile from this directory.

```bash
make check
make stage-vbd
make prod-vbd
```

`make check` vendors the current shared `e11/` package before validating imports and running tests.
`make build` exports runtime requirements and builds Linux arm64 dependencies in
Docker/Finch. Deploy targets run the complete DynamoDB Local/MinIO checks first;
they preserve TOML parameters and apply 180-day log retention after deployment.

### Email history

Signed-in students can use `/email` to list their archived course email.
Subjects open `/email/message?timestamp=...` in another tab. Both routes enforce
the existing session and user ownership, serve private non-cacheable responses,
and display escaped plain-text MIME content. See the parent CLI README for
archive storage, welcome behavior, and `make email-check` service configuration.

### Lab redirects

`/lab0` through `/lab8` redirect to the corresponding
`https://github.com/Harvard-CSCI-E-11/course/blob/main/doc/Lab_N.md` files.
These GitHub destinations are temporary until the labs are hosted on GitHub Pages;
the URLs are configured in the shared `e11.e11_common.LAB_CONFIG`.

### Authentication and session lifetime

Production and staging use separate session tables and host-only
`__Host-AuthSid` cookies (`Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`, no
`Domain`). Student subdomains cannot receive or set that cookie for a course
host. The old `AuthSid` cookie is ignored; browsers sign in again after rollout.
Pre-change session IDs are rejected even if supplied under the new cookie name
or via a SID-login link; only a fresh independent login can issue a host-bound
session record. Obsolete `AuthSid` cookies are expired at both host and parent
domain scopes when received. Old records retain their stored expiry for cleanup.
Cookie names, domains and the 120-day lifetime cannot be broadened by environment
variables. `COOKIE_SAMESITE` retains its existing SameSite override.

A successful authenticated request renews `session_expire` and DynamoDB's `ttl`
attribute to 120 days ahead and renews the cookie lifetime in the same response.
`session_last_authenticated` records that activity. An unexpired host-bound session missing activity/TTL metadata
acquires it on first use. This metadata migration never upgrades a pre-change SID
into a trusted credential. Expired sessions are rejected immediately;
DynamoDB TTL removes their records asynchronously. The five-minute scheduled
heartbeat also removes expired records, with conditional deletion protecting
sessions renewed after its scan.

Jinja escapes HTML templates by default; JavaScript values use HTML-safe JSON
and JSON in double-quoted attributes uses forced attribute escaping.
Production and staging explicitly share `ImageBucketName=csci-e-11`;
`IMAGE_BUCKET_NAME` is the corresponding Lambda runtime setting for image
uploads and deletion. No additional bucket is created. HTTP integrations use
30,000 ms, both home and leaderboard Lambdas use 30 seconds, and CLI grading defaults to 30 seconds.
