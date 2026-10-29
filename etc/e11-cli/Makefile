# e11/Makefile
#
# The e11 module runs on Python 3.14 on student machines and AWS Lambda.

# DynamoDB local stuff (see end)
DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000/
E11_VARS := AWS_ENDPOINT_URL_DYNAMODB=$(DYNAMODB_LOCAL_ENDPOINT)
REQ      := bin/DynamoDBLocal.jar


.PHONY: pytest lint clean check test man

.venv/pyvenv.cfg: pyproject.toml Makefile
	@uv sync --locked

lint: .venv/pyvenv.cfg
	uv run --locked pylint e11
	uv run --locked pyright e11

lint-all:
	make lint
	(cd lambda-home; make lint)
	(cd lambda-leaderboard; make lint)

check: .venv/pyvenv.cfg
	make lint
	uv run --locked pytest -q --cov=e11 --cov-report=term --cov-report=xml --junitxml=junit.xml -o junit_family=legacy tests/

check-all:
	make check
	(cd lambda-home; make check)
	(cd lambda-leaderboard; make check)

prod-all:
	(cd lambda-home; make prod-vbd)
	(cd lambda-leaderboard; make prod-vbd)


doc/e11.1:  .venv/pyvenv.cfg
	uv run --locked argparse-manpage --module e11.main --function get_parser \
		--author "Simson L. Garfinkel" \
		--project-name e11 \
		--url https://github.com/Harvard-CSCI-E-11/e11-course.git > doc/e11.1

man: doc/e11.1
	install -d $$HOME/.local/share/man/man1/
	install -m 0644 doc/e11.1 $$HOME/.local/share/man/man1/
	gzip -f $$HOME/.local/share/man/man1/e11.1
	mandb --quiet

clean:
	rm -f .coverage coverage.xml
	find . -name '__pycache__' -prune -exec rm -rf {} +
	rm -rf build/ dist/

distclean:
	make clean
	/bin/rm -rf .venv

install:
	uv tool install --force --python 3.14 .


tags:
	etags -l python */*.py */*/*.py */*/*/*.py
.PHONY: tags

################################################################
# DynamoDBLocal
# Installations are used by the CI pipeline and by local developers
# See https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html for info about DynamoDB (local version)

# installation:
DDBL_DOWNLOAD_URL:=https://d1ni2b6xgvw0s0.cloudfront.net/v2.x/dynamodb_local_latest.zip
bin/DynamoDBLocal.jar:
	test -f bin/dynamodb_local_latest.zip || curl $(DDBL_DOWNLOAD_URL) -o bin/dynamodb_local_latest.zip
	test -f bin/dynamodb_local_latest.zip || (echo could not download $(DDBL_DOWNLOAD_URL); exit 1)
	(cd bin; unzip -uq dynamodb_local_latest.zip DynamoDBLocal.jar 'DynamoDBLocal_lib/*')
	/bin/rm -f bin/dynamodb_local_latest.zip

# operation:
start_local_dynamodb: bin/DynamoDBLocal.jar
	bash bin/local_dynamodb_control.bash start

stop_local_dynamodb:  bin/DynamoDBLocal.jar
	bash bin/local_dynamodb_control.bash stop

list-tables:
	$(PT_VARS) aws dynamodb list-tables

dump-tables:
	for tn in "users" "sessions" ; do\
		echo $$tn:; \
		$(E11_VARS) aws dynamodb describe-table --table-name $$tn ; \
		$(E11_VARS) aws dynamodb scan --max-items 5 --table-name $$tn ; \
		done

.PHONY: ddb-backup ddb-view ddb-restore
ddb-backup: .venv/pyvenv.cfg
	@test -n "$(DDB_DIR)"
	@uv run --locked e11admin backup "$(DDB_DIR)" $(if $(DDB_TABLE),--table "$(DDB_TABLE)")

ddb-view: .venv/pyvenv.cfg
	@test -n "$(DDB_DIR)"
	@uv run --locked e11admin view "$(DDB_DIR)" $(if $(DDB_TABLE),--table "$(DDB_TABLE)")

ddb-restore: .venv/pyvenv.cfg
	@test -n "$(DDB_DIR)" && test "$(DDB_ALLOW_RESTORE)" = YES
	@uv run --locked e11admin restore "$(DDB_DIR)" $(if $(DDB_TABLE),--table "$(DDB_TABLE)")

# DNS cleanup: DDB_DIR supplies the step-3 export prefix. DNS_ZONE_EXPORT can
# override that input; DNS_KEEP names the keep-list and DNS_PLAN the saved plan.
# DNS_DOMAIN, DNS_ZONE_ID, and DNS_ACCOUNT_ID select and verify the destination.
# AWS_PROFILE uses normal AWS credentials; DNS_PROFILE optionally overrides it.
DNS_DOMAIN ?= csci-e-11.org
DNS_KEEP ?= dns-keep.txt
DNS_ZONE_EXPORT ?= $(if $(DDB_DIR),$(DDB_DIR)-route53.json)
DNS_PLAN ?= $(if $(DNS_ZONE_EXPORT),$(DNS_ZONE_EXPORT).delete-plan.json)
DNS_CLEANUP := e11/e11admin/end-of-term/cleanup_dns.py
DNS_ARGS = --domain "$(DNS_DOMAIN)" --zone-id "$(DNS_ZONE_ID)" --account-id "$(DNS_ACCOUNT_ID)" --keep "$(DNS_KEEP)" $(if $(DNS_PROFILE),--profile "$(DNS_PROFILE)")

.PHONY: dns-plan dns-delete dns-test dns-lint
dns-plan: .venv/pyvenv.cfg
	@test -n "$(DNS_DOMAIN)" && test -n "$(DNS_ZONE_ID)" && test -n "$(DNS_ACCOUNT_ID)" && test -n "$(DNS_ZONE_EXPORT)" && test -n "$(DNS_PLAN)" || { echo "Set DDB_DIR (or DNS_ZONE_EXPORT), DNS_ZONE_ID, and DNS_ACCOUNT_ID." >&2; exit 1; }
	@uv run --locked python $(DNS_CLEANUP) $(DNS_ARGS) --zone-export "$(DNS_ZONE_EXPORT)" --plan "$(DNS_PLAN)"

dns-delete: .venv/pyvenv.cfg
	@test -n "$(DNS_DOMAIN)" && test -n "$(DNS_ZONE_ID)" && test -n "$(DNS_ACCOUNT_ID)" && test -n "$(DNS_PLAN)" || { echo "Set DDB_DIR (or DNS_PLAN), DNS_ZONE_ID, and DNS_ACCOUNT_ID." >&2; exit 1; }
	@uv run --locked python $(DNS_CLEANUP) $(DNS_ARGS) --apply-plan "$(DNS_PLAN)"

dns-test: .venv/pyvenv.cfg
	uv run --locked pytest -q tests/test_cleanup_dns.py

dns-lint: .venv/pyvenv.cfg
	uv run --locked pylint $(DNS_CLEANUP)
	uv run --locked pyright $(DNS_CLEANUP)

# Public DNS logging uses AWS_PROFILE/DNS_PROFILE and the DNS destination above.
# DNS_LOG_GROUP overrides the existing/default group; retention is fixed at 180d.
# DNS_LOG_SINCE/UNTIL bound reports, NAME/STUDENT select hostnames, LIMIT caps rows,
# and FORMAT selects table, csv, or json. See README.md for exact variable names.
DNS_LOGGING := e11/e11admin/dns_logging.py
DNS_LOG_FORMAT ?= table
DNS_LOG_ARGS = --domain "$(DNS_DOMAIN)" --zone-id "$(DNS_ZONE_ID)" --format "$(DNS_LOG_FORMAT)" $(if $(DNS_ACCOUNT_ID),--account-id "$(DNS_ACCOUNT_ID)") $(if $(DNS_PROFILE),--profile "$(DNS_PROFILE)") $(if $(DNS_LOG_GROUP),--log-group "$(DNS_LOG_GROUP)")
DNS_LOG_VIEW_ARGS = $(if $(DNS_LOG_SINCE),--since "$(DNS_LOG_SINCE)") $(if $(DNS_LOG_UNTIL),--until "$(DNS_LOG_UNTIL)") $(if $(DNS_LOG_NAME),--name "$(DNS_LOG_NAME)") $(if $(DNS_LOG_STUDENT),--student "$(DNS_LOG_STUDENT)") $(if $(DNS_LOG_LIMIT),--limit "$(DNS_LOG_LIMIT)")

.PHONY: dns-logging-enable dns-logging-status dns-logging-verify dns-logs dns-log-report dns-logging-test dns-logging-lint
dns-logging-enable dns-logging-status dns-logging-verify: .venv/pyvenv.cfg
	@test -n "$(DNS_ZONE_ID)" || { echo "Set DNS_ZONE_ID to the public hosted-zone ID." >&2; exit 1; }
	@uv run --locked python $(DNS_LOGGING) $(patsubst dns-logging-%,%,$@) $(DNS_LOG_ARGS)

dns-logs dns-log-report: .venv/pyvenv.cfg
	@test -n "$(DNS_ZONE_ID)" || { echo "Set DNS_ZONE_ID to the public hosted-zone ID." >&2; exit 1; }
	@uv run --locked python $(DNS_LOGGING) $(if $(filter dns-logs,$@),events,report) $(DNS_LOG_ARGS) $(DNS_LOG_VIEW_ARGS)

dns-logging-test: .venv/pyvenv.cfg
	uv run --locked pytest -q tests/test_dns_logging.py

dns-logging-lint: .venv/pyvenv.cfg
	uv run --locked pylint $(DNS_LOGGING)
	uv run --locked pyright $(DNS_LOGGING)


.PHONY: start_local_dynamodb stop_local_dynamodb list-tables dump-demo-tables
