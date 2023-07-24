DATE		= $(shell date)
PYTHON		= $(shell poetry run which python 2>/dev/null || which python)
PKG_VERSION = $(shell poetry -s version)
BUILD_DATE  = $(shell date +'%B %d, %Y')
QPC_VAR_PROGRAM_NAME := $(or $(QPC_VAR_PROGRAM_NAME), "qpc")
QPC_VAR_PROGRAM_NAME_UPPER := $(shell echo $(QPC_VAR_PROGRAM_NAME) | tr '[:lower:]' '[:upper:]')

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords
BINDIR  = bin

OMIT_PATTERNS = */test*.py,*/.virtualenvs/*.py,*/virtualenvs/*.py,.tox/*.py
pandoc = pandoc

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help                to show this message"
	@echo "  install             to install the client egg"
	@echo "  clean               to remove client egg"
	@echo "  lint                to run all linters"
	@echo "  lint-ruff           to run the ruff linter"
	@echo "  lint-black          to run the black format checker"
	@echo "  lint-docs           to run rstcheck against docs"
	@echo "  test                to run unit tests"
	@echo "  test-coverage       to run unit tests and measure test coverage"
	@echo "  manpage             to build the manpage"
	@echo "  build-container     to build the quipucords-cli container image"

clean:
	-rm -rf dist/ build/ qpc.egg-info/

install:
	$(PYTHON) setup.py build -f
	$(PYTHON) setup.py install -f

lint: lint-ruff lint-black lint-docs

lint-ruff:
	poetry run ruff .

lint-black:
	poetry run black --diff --check .

lint-docs:
	poetry run rstcheck docs/source/man.rst

test:
	poetry run pytest

test-coverage:
	poetry run pytest --cov=qpc
	poetry run coverage report --show-missing
	poetry run coverage xml

generate-man:
	@export QPC_VAR_CURRENT_YEAR=$(shell date +'%Y') \
	&& export QPC_VAR_PROJECT=$${QPC_VAR_PROJECT:-Quipucords} \
	&& export QPC_VAR_PROGRAM_NAME=$${QPC_VAR_PROGRAM_NAME:-qpc} \
	&& poetry run jinja -X QPC_VAR docs/source/man.j2 $(ARGS)

update-man.rst:
	$(MAKE) generate-man ARGS="-o docs/source/man.rst"

manpage-test:
	@poetry run $(MAKE) --no-print-directory generate-man | diff -u docs/source/man.rst -

manpage:
	@$(MAKE) --no-print-directory generate-man | \
	$(pandoc) -s - \
	  --standalone -t man -o docs/$(QPC_VAR_PROGRAM_NAME).1\
	  --variable=section:1\
	  --variable=date:'$(BUILD_DATE)'\
	  --variable=footer:'version $(PKG_VERSION)'\
	  --variable=header:'$(QPC_VAR_PROGRAM_NAME_UPPER) Command Line Guide'

build-container:
	podman build -t ${QPC_VAR_PROGRAM_NAME} .
