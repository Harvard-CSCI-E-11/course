#
# This is a Unix Makefile for lab4
#
# It is different from lab3, in that:
# - we now provide targets for automatically installing the lab4 service the lab4 nginx site
# -

################################################################
# Installation targets
#
# Create the virtual environment
export LAB=lab4
export PORT=8004

PYTHON=.venv/bin/python3

$(PYTHON):
	uv sync --locked
	npm install

#
# Install the lab4.services file
install-lab4-service: $(PYTHON)
	sudo install lab4.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable lab4
	sudo systemctl start lab4

install-lab4-nginx:
	@echo TODO - install the new site and run lets encrypt

################################################################
# Application targets
# Run the application locally for testing
# Note: your local machine must be authorized for your AWS account with the `aws` command.
local-app: $(PYTHON)
	uv run --locked flask --app server.main:app run --debug --port 8004 --reload

# Print help for the application
help: $(PYTHON)
	uv run --locked flask --app server.main:app --help

# Create a new database
init-db: $(PYTHON)
	uv run --locked flask --app server.main:app init-db

# Wipe the database and start over
wipe-db: $(PYTHON)
	uv run --locked flask --app server.main:app wipe-db
	make init-db

# Generate a new api-key
# Note the '@' so that the `uv run flask...` command is not included in the output
new-apikey: $(PYTHON)
	@uv run --locked flask --app server.main:app new-apikey

# Dump the database
dump-db: $(PYTHON)
	uv run --locked flask --app server.main:app dump-db

# dump the listing for an AI
dump-listing:
	/bin/rm -f listing.txt
	# Exclude large dependency/runtime directories from the tree output
	tree -I 'node_modules|.venv|instance' > listing.txt
	# Limit files to project-owned code and templates
	for fn in Makefile \
		server/*.py server/*/*.py \
		server/templates/*.html server/templates/*/*.html \
		server/static/*.js server/static/*/*.js \
		tools/*.py tools/*.js ; \
		do echo "== $$fn ==" >> listing.txt ; cat $$fn >> listing.txt; done

#
# Software engineering targets

lint: $(PYTHON)
	uv run --locked pylint server
	uv run --locked djlint --profile=jinja --reformat server/templates/*html
	npx eslint -c tools/eslint.config.mjs server/static


distclean:
	/bin/rm -rf .venv
	/bin/rm -f instance/message_board.db

# make venv always run, even if it exists
.PHONY: local-app help init-db wipe-db new-apikey dump-db lint distclean dump-listing
.PHONY: install-lab4-service
