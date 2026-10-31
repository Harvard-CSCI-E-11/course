lint:
	sam validate --config-file samconfig.toml -t template.yaml --lint

distclean:
	/bin/rm -rf .venv

# Course reset pins fas/us-east-1; these targets do not inherit endpoint overrides.
# DDB_EMPTY=1 explicitly permits deletion; its absence leaves only inventory available.
# DDB_EMPTY_TEST_PORT selects the isolated DynamoDB Local integration-test port.
DDB_EMPTY_TEST_PORT ?= 18001
.PHONY: ddb-empty-plan ddb-empty ddb-empty-test
ddb-empty-plan: ../.venv/pyvenv.cfg
	uv run --project .. --locked python empty_course_tables.py

ddb-empty: ../.venv/pyvenv.cfg
	@test "$(DDB_EMPTY)" = 1 || { echo "Deletion requires DDB_EMPTY=1" >&2; exit 1; }
	DDB_EMPTY="$(DDB_EMPTY)" uv run --project .. --locked python empty_course_tables.py --apply

ddb-empty-test: ../.venv/pyvenv.cfg ../bin/DynamoDBLocal.jar
	@set -eu; mkdir -p var; \
	java -Djava.library.path=../bin/DynamoDBLocal_lib -jar ../bin/DynamoDBLocal.jar -inMemory -sharedDb -port $(DDB_EMPTY_TEST_PORT) > var/ddb-empty-test.log 2>&1 & ddb_pid=$$!; \
	trap 'kill $$ddb_pid 2>/dev/null || true' EXIT INT TERM; \
	for attempt in $$(seq 1 30); do \
	  kill -0 $$ddb_pid; \
	  if curl -s http://127.0.0.1:$(DDB_EMPTY_TEST_PORT)/ > /dev/null; then break; fi; \
	  sleep 1; \
	done; \
	AWS_ACCESS_KEY_ID=test AWS_SECRET_ACCESS_KEY=test AWS_DEFAULT_REGION=us-east-1 AWS_ENDPOINT_URL_DYNAMODB=http://127.0.0.1:$(DDB_EMPTY_TEST_PORT) \
	uv run --project .. --locked python -m pytest -q tests/test_empty_course_tables.py

../.venv/pyvenv.cfg: ../pyproject.toml ../Makefile
	$(MAKE) -C .. .venv/pyvenv.cfg

../bin/DynamoDBLocal.jar:
	$(MAKE) -C .. bin/DynamoDBLocal.jar
