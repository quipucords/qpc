DATE		= $(shell date)
PYTHON		= $(shell poetry run which python 2>/dev/null || which python)
PKG_VERSION = $(shell poetry -s version)
BUILD_DATE  = $(shell date +'%B %d, %Y')
PARALLEL_NUM ?= $(shell python -c 'import multiprocessing as m;print(int(max(m.cpu_count()/2, 2)))')
QPC_VAR_PROGRAM_NAME := $(or $(QPC_VAR_PROGRAM_NAME), qpc)
QPC_VAR_PROGRAM_NAME_UPPER := $(shell echo $(QPC_VAR_PROGRAM_NAME) | tr '[:lower:]' '[:upper:]')

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords
BINDIR  = bin

OMIT_PATTERNS = */test*.py,*/.virtualenvs/*.py,*/virtualenvs/*.py,.tox/*.py
SPHINX_BUILD = $(shell poetry run which sphinx-build)

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
	@echo "  lock-requirements   to lock all python dependencies"
	@echo "  update-requirements to update all python dependencies"
	@echo "  check-requirements  to check python dependency files"

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
	&& poetry run python docs/jinja-render.py -e '^QPC_VAR.*' -t docs/source/man.j2 $(ARGS)

update-man.rst:
	$(MAKE) generate-man ARGS="-o docs/source/man.rst"

manpage-test:
	@poetry run $(MAKE) --no-print-directory generate-man | diff -u docs/source/man.rst -

manpage:
	@$(MAKE) --no-print-directory update-man.rst
	$(SPHINX_BUILD) -b man \
	  -D project='$(QPC_VAR_PROGRAM_NAME)' \
	  -D release='$(PKG_VERSION)' \
	  -D today='$(BUILD_DATE)' \
	  docs docs/_build

build-container:
	podman build -t ${QPC_VAR_PROGRAM_NAME} .

lock-requirements: lock-main-requirements lock-build-requirements

lock-main-requirements:
	poetry lock --no-update
	poetry export -f requirements.txt --only=main --without-hashes -o requirements.txt

lock-build-requirements:
	poetry run pybuild-deps compile -o requirements-build.txt requirements.txt

update-requirements:
	poetry update --no-cache
	$(MAKE) lock-requirements PIP_COMPILE_ARGS="--upgrade"

check-requirements:
ifeq ($(shell git diff --exit-code requirements.txt >/dev/null 2>&1; echo $$?), 0)
	@exit 0
else
	@echo "requirements.txt not in sync with poetry.lock. Run 'make lock-requirements' and commit the changes"
	@exit 1
endif
