# Build the leaderboard with uv-managed runtime dependencies and a vendored e11 wheel.
# SAM reads the exported manifest at the CodeUri root, src/requirements.txt.
# Container builds produce Linux arm64 dependencies rather than workstation wheels.
# Deployments preserve TOML overrides and add a UTC release timestamp.
# AWS_PROFILE/AWS_REGION select the account credentials and region for log retention.
# LOG_LEVEL selects application logging; boto3/botocore DEBUG stays suppressed.
# STAGE_NAME and DEPLOYMENT_TIMESTAMP label the deployed version report.
AWS_PROFILE ?= fas
AWS_REGION ?= us-east-1

.PHONY: install validate lint check test clean requirements build
install:
	uv sync --locked

validate:
	sam validate --config-file samconfig-prod.toml -t template.yaml --lint

check: install vend-e11
	uv run --locked pytest --log-cli-level=INFO

lint: install vend-e11 validate
	PYTHONPATH=src uv run --locked pylint leaderboard_app

local-debug: install vend-e11
	PYTHONPATH=src uv run --locked python -c 'from leaderboard_app.flask_app import app; app.run(debug=True)'

# https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/using-sam-cli-sync.html
sam-sync: install
	sam sync --code --watch

.PHONY: prod-vbd stage-vbd
build: requirements vend-e11
	sam build --parallel --use-container --config-file samconfig-prod.toml -t template.yaml

prod-vbd: template.yaml samconfig-prod.toml
	$(MAKE) -C .. email-check
	$(MAKE) build
	uv run --locked python ../e11/e11admin/sam_deploy.py --config samconfig-prod.toml --template .aws-sam/build/template.yaml
	$(MAKE) -C .. lambda-log-retention LOG_STACK=leaderboard AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION)
	curl --silent  https://leaderboard.csci-e-11.org/ | head -3

prod-tail:
	sam logs --stack-name leaderboard --name LeaderboardFlaskFunction --tail   --region us-east-1   --profile fas

# This target generates the requirements.txt for SAM to use
requirements: src/requirements.txt

src/requirements.txt: uv.lock pyproject.toml Makefile
	@echo "--- Exporting requirements.txt from uv ---"
	uv export --locked --no-dev --no-emit-project --no-emit-package e11 --no-hashes --format requirements.txt --output-file $@ > /dev/null

# Useful functions
list-cloud-resources:
	aws cloudformation list-stack-resources \
	  --stack-name leaderboard --region us-east-1 --profile fas \
	  --query "StackResourceSummaries[?ResourceType=='AWS::ApiGatewayV2::DomainName'].[LogicalResourceId,PhysicalResourceId,ResourceStatus]" \
	  --output table


# --- Custom Vendoring
.PHONY: vend-e11
vend-e11: install
	@echo "Building the shared e11 wheel via uv"
	$(MAKE) -C .. wheel
	uv pip install --no-deps --reinstall --target src "$$(ls -t ../dist/e11-*.whl | head -1)"
	/bin/rm -f src/leaderboard_app/e11.whl

distclean:
	/bin/rm -rf .venv
	/bin/rm -f instance/message_board.db
	/bin/rm -f src/requirements.txt src/leaderboard_app/requirements.txt
