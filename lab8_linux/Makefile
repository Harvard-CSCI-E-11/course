################################################################
# Installation targets
#
# Create the virtual environment for running lab7 linux client

export LAB=lab8

PYTHON=.venv/bin/python3
install: $(PYTHON)

$(PYTHON):
	uv sync --locked

lint: $(PYTHON)
	uv run --locked pylint *.py
	uv run --locked pyright *.py

distclean:
	/bin/rm -rf .venv

.PHONY: distclean lint memento-install
