#
# This is a Unix Makefile for Lab 8
# We use python to install djlint which is used to check the HTML files

PYTHON=.venv/bin/python3
install: $(PYTHON)

$(PYTHON):
	uv sync --locked

pub1:
	cp camera1.py /Volumes/CIRCUITPY/code.py

pub2:
	cp camera2.py /Volumes/CIRCUITPY/code.py

pub3:
	cp camera3.py /Volumes/CIRCUITPY/code.py


memento-install: $(PYTHON) requirements_cp.txt
	uv run --locked circup install -r requirements_cp.txt

lint: $(PYTHON)
	uv run --locked pylint *.py

# Don't have pyright working yet here.
#uv run --locked pyright *.py

distclean:
	/bin/rm -rf .venv

.PHONY: distclean lint memento-install
