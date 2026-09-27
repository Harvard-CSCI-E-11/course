################################################################
# Installation targets
#
# Create the virtual environment for running circuitpython tools

export LAB=lab7

PYTHON=.venv/bin/python3
install: $(PYTHON)

$(PYTHON):
	uv sync --locked

memento-install: $(PYTHON) requirements_cp.txt
	uv run --locked circup install -r requirements_cp.txt

lint: $(PYTHON)
	uv run --locked pylint *.py
	uv run --locked pyright *.py

distclean:
	/bin/rm -rf .venv

.PHONY: distclean lint memento-install
