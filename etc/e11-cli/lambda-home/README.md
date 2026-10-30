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
