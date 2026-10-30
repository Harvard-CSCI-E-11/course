# Staging and backup environment

`https://stage.csci-e-11.org/` is an independent Lambda deployment used as a backup
and for real course testing. It intentionally writes production data; a complete
duplicate data system is not intended.

| Setting | Production | Staging |
| --- | --- | --- |
| Stack | `home-app-prod` | `home-app-stage` |
| API stage | `prod` | `stage` |
| Public host | `csci-e-11.org` | `stage.csci-e-11.org` |
| Session table | `home-app-prod-sessions` | `home-app-stage-sessions` |

Both deployments share `e11-users`, `Leaderboard`, the course Route53 zone, SES,
and the OIDC/SSH/SQS secrets. Application image/email operations use `csci-e-11`.
The deployed staging `ImageBucketName` currently differs (`cscie-11`); reconcile
that existing parameter/IAM/event-rule drift explicitly before testing images.

Sessions are separate. The current parent-domain cookie collides between stacks;
logging into one can replace the other's cookie. The host-only cookie migration
is a proposal in the root TODO, not part of the uv/grading update.

One parameterized `template.yaml` and the two `samconfig-*.toml` files define both
stacks. There are no generated template parts or build-stage/deploy-stage targets.
From `etc/e11-cli/lambda-home`, with Docker/Finch running:

```bash
make build                    # Build only; no AWS deployment
# Once the requested deployment is authorized:
make stage-vbd                # Validate, build, deploy staging, set log retention
make prod-vbd                 # Validate, build, deploy production, set log retention
```

The deploy targets run the complete local DynamoDB/MinIO suite, preserve TOML
parameter overrides, add a UTC timestamp, and set 180-day Lambda-log retention.
Tests use isolated local data; actual staging requests change shared production
course data and can send real email. `PUBLIC_DOMAIN_NAME` selects the OIDC callback
host; both callback URLs must be registered with the provider. A successful real
stage login remains an acceptance check.
