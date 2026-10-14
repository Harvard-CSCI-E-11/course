# e11/Makefile
#
# The e11 module runs on Python 3.14 on student machines and AWS Lambda.

# DynamoDB local stuff (see end)
DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000/
E11_VARS := AWS_ENDPOINT_URL_DYNAMODB=$(DYNAMODB_LOCAL_ENDPOINT)
REQ      := bin/DynamoDBLocal.jar


.PHONY: pytest lint clean check test man

.venv/pyvenv.cfg: pyproject.toml Makefile
	uv sync --locked

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

# DNS cleanup requires an explicit student-name list and a reviewed plan hash.
DNS_CLEANUP := e11/e11admin/end-of-term/cleanup_dns.py
DNS_ARGS = --domain "$(DNS_DOMAIN)" --zone-id "$(DNS_ZONE_ID)" --account-id "$(DNS_ACCOUNT_ID)" $(if $(DNS_PROFILE),--profile "$(DNS_PROFILE)")

.PHONY: dns-plan dns-apply
dns-plan: .venv/pyvenv.cfg
	@test -n "$(DNS_DOMAIN)" && test -n "$(DNS_ZONE_ID)" && test -n "$(DNS_ACCOUNT_ID)" && test -n "$(DNS_NAMES)" && test -n "$(DNS_PLAN)"
	uv run --locked python $(DNS_CLEANUP) $(DNS_ARGS) --names "$(DNS_NAMES)" --plan "$(DNS_PLAN)" $(if $(DNS_ZONE_EXPORT),--zone-export "$(DNS_ZONE_EXPORT)")

dns-apply: .venv/pyvenv.cfg
	@test -n "$(DNS_DOMAIN)" && test -n "$(DNS_ZONE_ID)" && test -n "$(DNS_ACCOUNT_ID)" && test -n "$(DNS_PLAN)" && test -n "$(DNS_SHA256)"
	uv run --locked python $(DNS_CLEANUP) $(DNS_ARGS) --apply-plan "$(DNS_PLAN)" --sha256 "$(DNS_SHA256)"


.PHONY: start_local_dynamodb stop_local_dynamodb list-tables dump-demo-tables
