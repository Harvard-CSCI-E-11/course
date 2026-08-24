#
# Makefile for lab_common
#
# These modules are used by more than one lab
#
# The best Makefile tutorial we have found is here:
# https://opensource.com/article/18/8/what-how-makefile
#
# For background, see:
# https://en.wikipedia.org/wiki/Make_(software)
#
# This Makefile assumes pylint is your path.
# create_log_db.py can be run through the python that's preinstalled with the OS.

export LAB=lab_common
PYTHON=.venv/bin/python3

$(PYTHON):
	uv sync --locked

lint: $(PYTHON)
	uv run --locked pylint *.py

check: $(PYTHON)
	@echo nothing to check

distclean:
	@echo already clean


.PHONY: distclean lint
