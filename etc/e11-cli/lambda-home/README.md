# Lambda Home

`lambda-home` is the AWS SAM application that serves the CSCI E-11 student dashboard, registration API, grading API, OIDC login flow, and upload callbacks.

## Layout

```text
lambda-home/
├── src/home_app/          # Lambda application package
├── src/home_app/e11.whl   # Vendored shared e11 package built from ../e11/
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

### Email history

Signed-in students can use `/email` to list their archived course email.
Subjects open `/email/message?timestamp=...` in another tab. Both routes enforce
the existing session and user ownership, serve private non-cacheable responses,
and display escaped plain-text MIME content. See the parent CLI README for
archive storage, welcome behavior, and `make email-check` service configuration.
