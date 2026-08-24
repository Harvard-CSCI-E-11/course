#
# This is a Unix Makefile for Lab 2
#
# We use python to install djlint which is used to check the HTML files
# The variables LAB and PORT are set, but they aren't used.
#
# This Makefile exists to check the HTML for correctness.
# We expect that you will move the files as specified below:
#
# cp $HOME/spring26/lab2/public.html /var/www/html/
# cp $HOME/spring26/lab2/confidential.html /var/www/html/confidential/


export LAB=lab2
export PORT=8002

PYTHON=.venv/bin/python3
install: $(PYTHON)

$(PYTHON):
	uv sync --locked

lint: $(PYTHON)
	uv run --locked python -m djlint .
	uv run --locked pyright *.py

distclean:
	@echo already clean


.PHONY: distclean lint
