DATE		= $(shell date)
PYTHON		= $(shell which python)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords

BINDIR  = bin

OMIT_PATTERNS = */test*.py,*/.virtualenvs/*.py,*/virtualenvs/*.py,.tox/*.py

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help                to show this message"
	@echo "  all                 to execute all following targets (except test)"
	@echo "  lint                to run all linters"
	@echo "  clean               to remove postgres docker container"
	@echo "  lint-flake8         to run the flake8 linter"
	@echo "  lint-pylint         to run the pylint linter"
	@echo "  test                to run unit tests"
	@echo "  test-coverage       to run unit tests and measure test coverage"
	@echo "  swagger-valid       to run swagger-cli validation"
	@echo "  setup-postgres      to create a default postgres container"
	@echo "  server-init         to run server initializion steps"
	@echo "  serve               to run the server with default db"
	@echo "  manpage             to build the manpage"
	@echo "  html                to build the docs"
	@echo "  build-ui       to build ui and place result in django server"

all: build lint test-coverage

build: clean
	$(PYTHON) setup.py build -f

clean:
	-rm -rf dist/ build/ qpc.egg-info/

install: build
	$(PYTHON) setup.py install -f

lint:
	tox -e lint

test:
	tox -e py36

test-coverage:
	coverage run -m unittest discover qpc/ -v
	coverage report -m --omit $(OMIT_PATTERNS)
	echo $(OMIT_PATTERNS)

html:
	@cd docs; $(MAKE) html

manpage:
	@mkdir -p build
	pandoc docs/source/man.rst \
	  --standalone -t man -o build/qpc.1 \
	  --variable=section:1 \
	  --variable=date:'July 17, 2018' \
	  --variable=footer:'version 1.0.0' \
	  --variable=header:'QPC Command Line Guide'
