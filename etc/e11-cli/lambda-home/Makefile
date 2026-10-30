# ===== e11 home Makefile =====
# Uses uv for dependency management and Make for SAM/AWS task running.
#
# Note: everything must be in same AWS region

# SAM/AWS Configuration (unchanged)
STACK_PROD      ?= home-app-prod
STACK_STAGE     ?= home-app-stage
CAPS            ?= CAPABILITY_IAM CAPABILITY_AUTO_EXPAND
AWS_REGION      ?= us-east-1
PROFILE         ?= fas
DJLINT_FLAGS    ?= --profile=jinja --lint --quiet --ignore J004,J018
TEMPLATE_DIR    := src/home_app/templates
S3_BUCKET       ?= csci-e-11
AWS_PROFILE     ?= fas
ROOT_DOMAIN     ?= csci-e-11.org
# SAM_CONFIG chooses the build's TOML settings; deploy targets select it explicitly.
SAM_CONFIG      ?= samconfig-prod.toml

# Shell Configuration (unchanged)
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

# Environment setup (unchanged)
export PIP_DISABLE_PIP_VERSION_CHECK=1
export PIP_NO_INPUT=1
export PYTHONDONTWRITEBYTECODE=1

# --- uv-based Targets ---

.PHONY: install format lint check test clean
install:
	@echo "--- Installing dependencies with uv ---"
	uv sync --locked

format: install
	uv run --locked ruff check --fix
	uv run --locked ruff format

# https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html
install-sam-ubuntu:
	curl -L https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip -o aws-sam-cli-linux-x86_64.zip
	unzip aws-sam-cli-linux-x86_64.zip -d sam-installation
	sudo ./sam-installation/install
	sam --version
	/bin/rm -rf aws-sam-cli-linux-x86_64.zip sam-installation

lint: vend-e11
	@echo "--- Validating imports from the installed runtime package ---"
	uv run --locked pytest -xvs tests/test_import_validation.py
	uv run --locked djlint $(DJLINT_FLAGS) $(TEMPLATE_DIR)/*.html
	uv run --locked ruff check
	uv run --locked pylint src
	uv run --locked pyright src
	sam validate --config-file samconfig-prod.toml -t template.yaml --lint
	sam validate --config-file samconfig-stage.toml -t template.yaml --lint

check: vend-e11 lint
	@echo "--- Running tests with pytest ---"
	uv run --locked pytest -q --cov=. --cov-report=term --cov-report=xml --junitxml=junit.xml -o junit_family=legacy --log-cli-level=DEBUG tests/

.PHONY: test-email
test-email: vend-e11
	uv run --locked pytest tests/test_email_archive.py

# This target generates the requirements.txt for SAM to use
.PHONY: requirements build
requirements: src/requirements.txt

src/requirements.txt: uv.lock pyproject.toml Makefile
	@echo "--- Exporting requirements.txt from uv ---"
	uv export --locked --no-dev --no-emit-project --no-emit-package e11 --no-hashes --format requirements.txt --output-file $@ > /dev/null

distclean:
	@echo "--- Cleaning up project files ---"
	/bin/rm -rf .venv
	/bin/rm -rf .aws-sam/build
	/bin/rm -f src/requirements.txt
	/bin/rm -f lambda.zip
	/bin/rm -rf .mypy_cache .pytest_cache
	find . -type d -name "__pycache__" -exec rm -rf {} +

# --- Custom Vendoring
.PHONY: vend-e11
vend-e11: install
	@echo "Building the shared e11 wheel via uv"
	( cd .. && uv build --wheel --out-dir dist )
	uv pip install --no-deps --reinstall --target src "$$(ls -t ../dist/e11-*.whl | head -1)"
	/bin/rm -f src/home_app/e11.whl

# --- AWS SAM/CLI Targets
# These are deployment tasks, perfect for Make.
# They depend on the uv-based targets above.

.PHONY: prod-vbd stage-vbd
build: requirements vend-e11
	sam build --parallel --use-container --config-file $(SAM_CONFIG) -t template.yaml

prod-vbd: template.yaml samconfig-prod.toml
	$(MAKE) -C .. email-check
	$(MAKE) build SAM_CONFIG=samconfig-prod.toml
	uv run --locked python ../e11/e11admin/sam_deploy.py --config samconfig-prod.toml --template .aws-sam/build/template.yaml
	$(MAKE) -C .. lambda-log-retention LOG_STACK=$(STACK_PROD) AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION)
	curl --silent  https://$(ROOT_DOMAIN)/ | head -3

stage-vbd: template.yaml samconfig-stage.toml
	$(MAKE) -C .. email-check
	$(MAKE) build SAM_CONFIG=samconfig-stage.toml
	uv run --locked python ../e11/e11admin/sam_deploy.py --config samconfig-stage.toml --template .aws-sam/build/template.yaml
	$(MAKE) -C .. lambda-log-retention LOG_STACK=$(STACK_STAGE) AWS_PROFILE=$(AWS_PROFILE) AWS_REGION=$(AWS_REGION)
	curl --silent  https://stage.$(ROOT_DOMAIN)/ | head -3

# Show function names
.PHONY: functions
functions:
	@echo "Production function:"
	aws cloudformation describe-stacks --stack-name $(STACK_PROD) --region $(AWS_REGION) --profile $(AWS_PROFILE) \
		--query 'Stacks[0].Outputs[?OutputKey==`HomeFunction`].OutputValue' --output text 2>/dev/null || echo "Stack not found"
	@echo "Stage function:"
	aws cloudformation describe-stacks --stack-name $(STACK_STAGE) --region $(AWS_REGION) --profile $(AWS_PROFILE) \
		--query 'Stacks[0].Outputs[?OutputKey==`HomeFunction`].OutputValue' --output text 2>/dev/null || echo "Stack not found"

# Tail logs
.PHONY: prod-tail
prod-tail:
	 sam logs --stack-name $(STACK_PROD) --name E11HomeFunction --tail  --region $(AWS_REGION)

# Tail stage logs (separate stack)
.PHONY: stage-tail
stage-tail:
	@echo "Tailing stage logs..."
	@aws logs tail "/aws/lambda/$$(aws cloudformation describe-stacks --stack-name $(STACK_STAGE) --region $(AWS_REGION) --profile $(AWS_PROFILE) \
		--query 'Stacks[0].Outputs[?OutputKey==`HomeFunction`].OutputValue' --output text)" \
		--since 15m --follow --region $(AWS_REGION) --profile $(AWS_PROFILE)

# Download deployed Lambda package for inspection
.PHONY: fetch-zip-prod
fetch-zip-prod:
	@FUNC=$$(aws cloudformation describe-stacks \
		--stack-name $(STACK_PROD) \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--query 'Stacks[0].Outputs[?OutputKey==`HomeFunction`].OutputValue' \
		--output text); \
	echo "Fetching deployment package for $$FUNC..."; \
	URL=$$(aws lambda get-function --function-name $$FUNC \
		--region $(AWS_REGION) \
		--profile $(AWS_PROFILE) \
		--query 'Code.Location' --output text); \
	/bin/rm -f lambda.zip && curl -sSL $$URL -o lambda.zip && ls -l lambda.zip && \
	echo "Deployed package extracted to lambda-package-prod/"

# Show stage URL
.PHONY: urls
urls:
	@echo "Production URL: https://$(ROOT_DOMAIN).org/"
	@echo "Stage URL: https://stage.$(ROOT_DOMAIN).org/"

# Show deployment info
.PHONY: info
info:
	@echo "Production Stack: $(STACK_PROD)"
	@echo "Stage Stack: $(STACK_STAGE)"
	@echo "Region: $(AWS_REGION)"
	@echo "Profile: $(AWS_PROFILE)"
	@echo ""
	@echo "Environments:"
	@echo "  Production: https://$(ROOT_DOMAIN).org/"
	@echo "  Stage:    https://stage.$(ROOT_DOMAIN).org/"
	@echo ""
	@echo "Deployment Options:"
	@echo "  make deploy          - Deploy stage only (default)"
	@echo "  make deploy-prod     - Deploy production only"
	@echo "  make deploy-stage    - Deploy stage only (same as deploy)"
	@echo ""
	@echo "Template Management:"
	@echo "  make template.yaml     - Generate production template"
	@echo "  make template-stage.yaml - Generate stage template"
	@echo ""
	@echo "Debugging:"
	@echo "  make functions      - Show function names from stacks"
	@echo "  make tail           - Tail production logs"
	@echo "  make tail-stage     - Tail stage logs"


#
# Validate S3 rules
#
s3-install-rules:
	aws s3api --profile $(AWS_PROFILE) put-bucket-notification-configuration \
	    --bucket $(S3_BUCKET) \
	    --notification-configuration '{ "EventBridgeConfiguration": {} }'

s3-validate-rules-and-region:
	aws s3api --profile $(AWS_PROFILE) get-bucket-notification-configuration --bucket $(S3_BUCKET) | \
		grep EventBridgeConfiguration && echo "✅ EventBridge is ENABLED"
	aws --profile=$(AWS_PROFILE) s3api get-bucket-location --bucket $(S3_BUCKET) | sed s/null/$(AWS_REGION)/ | grep $(AWS_REGION) && echo "✅ S3 bucket in correct region"
