#
# Master makefile to check all of the projects in this repo.
#

PYPROJECT_DIRS := \
	lab1 lab2 lab3 lab4 lab5 lab6 lab7_linux lab7_memento \
	lab8_linux lab8_memento lab_common \
	etc/e11-cli etc/e11-cli/lambda-home etc/e11-cli/lambda-leaderboard
LINTDIRS := $(PYPROJECT_DIRS)
GENERATED_REQUIREMENTS := \
	etc/e11-cli/lambda-home/src/requirements.txt \
	etc/e11-cli/lambda-leaderboard/src/requirements.txt \
	etc/e11-cli/lambda-leaderboard/src/leaderboard_app/requirements.txt

lint-all:
	@fail=0; \
	for dir in $(LINTDIRS); do \
		printf "Linting %s... \033[K\r" "$$dir"; \
		if ! out=$$(cd $$dir && make -s lint </dev/null 2>&1); then \
			printf "\n"; \
			echo "=== $$dir ==="; \
			echo "$$out"; \
			fail=1; \
		fi; \
	done; \
	if [ $$fail -eq 1 ]; then \
		printf "Linting failed.\033[K\n"; \
		exit 1; \
	else \
		printf "Linting complete.\033[K\n"; \
	fi

check-all:
	$(MAKE) lint-all
	$(MAKE) -C etc/e11-cli check-all

# DNS settings are documented in etc/e11-cli/README.md; command-line variables
# and exported environment variables are passed to the administration Makefile.
dns-plan dns-delete dns-test dns-lint:
	$(MAKE) -C etc/e11-cli $@

update-all:
	for dir in $(PYPROJECT_DIRS) ; do (echo "=== $$dir ===" ; cd $$dir && uv lock --upgrade) ; done

sync-all:
	for dir in $(PYPROJECT_DIRS) ; do (echo "=== $$dir ===" ; cd $$dir && uv sync --locked) ; done

lock-all:
	for dir in $(PYPROJECT_DIRS) ; do (echo "=== $$dir ===" ; cd $$dir && uv lock) ; done

install:
	$(MAKE) -C etc/e11-cli lint
	uv tool install --force ./etc/e11-cli

clean-all:
	for name in node_modules .venv __pycache__ .pytest_cache .aws-sam '*.egg-info' coverage.xml htmlcov; do find . -type d -name "$$name" -print0 | xargs -0 rm -rf ; done
	/bin/rm -f $(GENERATED_REQUIREMENTS)

distclean-all: clean-all
.PHONY: lint-all check-all update-all sync-all lock-all install clean-all distclean-all dns-plan dns-delete dns-test dns-lint
