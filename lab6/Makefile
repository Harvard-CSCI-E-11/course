# This is a Unix Makefile for lab6
#
# It is different from lab5, in that:
# -
# -

################################################################
# Installation targets
#
# Create the virtual environment
export LAB=lab6
export PORT=8006

PYTHON=.venv/bin/python3
$(PYTHON):
	uv sync --locked
	npm install

#
# Install the lab4.services file
install-lab6-service:
	sudo install lab6.service /etc/systemd/system/
	sudo systemctl daemon-reload
	sudo systemctl enable lab6
	sudo systemctl start lab6

install-lab6-nginx:
	@echo TODO - install the new site and run lets encrypt


################################################################
# Application targets
# Run the application locally for testing
# Note: your local machine must be authorized for your AWS account with the `aws` command.
local-app: $(PYTHON)
	uv run --locked flask --app server.main:app run --debug --port 8006 --reload

# Print help for the application
help: $(PYTHON)
	uv run --locked flask --app server.main:app --help

# Create a new database
init-db: $(PYTHON)
	@uv run --locked flask --app server.main:app init-db

# Wipe the database and start over
wipe-db: $(PYTHON)
	uv run --locked flask --app server.main:app wipe-db
	make init-db

# Generate a new api-key
new-apikey: $(PYTHON)
	@uv run --locked flask --app server.main:app new-apikey

# Dump the database
dump-db: $(PYTHON)
	uv run --locked flask --app server.main:app dump-db

#
# Software engineering targets

lint: $(PYTHON)
	uv run --locked pylint server
	uv run --locked pyright *.py

distclean:
	/bin/rm -rf .venv
	/bin/rm -f instance/message_board.db

# make .venv always run, even if it exists
.PHONY: local-app help init-db wipe-db new-apikey dump-db lint distclean
.PHONY: install-lab6-service init-s3

#### lab5 additions follow

# Create the s3 bucket and establish the CORS policy
init-s3:
	uv run --locked flask --app server.main:app init-s3
