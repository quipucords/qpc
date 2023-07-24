DATE		= $(shell date)
PYTHON		= $(shell poetry run which python 2>/dev/null || which python)
PKG_VERSION = $(shell poetry -s version)
BUILD_DATE  = $(shell date +'%B %d, %Y')
PARALLEL_NUM ?= $(shell python -c 'import multiprocessing as m;print(int(max(m.cpu_count()/2, 2)))')
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

lock-requirements: lock-main-requirements
	rm -f requirements-build.txt requirements-build.in
	$(MAKE) search-build-requirements
	$(MAKE) lock-build-requirements
	# run another rounds of search/lock for build requirements
	# (build dependencies also have build dependencies after all :)
	$(MAKE) search-build-requirements
	$(MAKE) lock-build-requirements
	$(MAKE) search-build-requirements
	$(MAKE) lock-build-requirements
	mv requirements-build.in tmp-requirements-build.in
	cat tmp-requirements-build.in | sed 's/ //g' | sort -u  > requirements-build.in
	rm tmp-requirements-build.in

lock-main-requirements:
	poetry lock --no-update
	poetry export -f requirements.txt --only=main --without-hashes -o requirements.txt

lock-build-requirements:
	poetry run pip-compile $(PIP_COMPILE_ARGS) -r --resolver=backtracking --quiet --allow-unsafe --output-file=requirements-build.txt requirements-build.in

search-build-requirements:
	cat requirements*.txt | grep -vE '(^ )|(#)' | awk '{print $$1}' | sed 's/==/ /' | \
	xargs -P$(PARALLEL_NUM) -n2 poetry run pybuild-deps find-build-deps 2> /dev/null | \
	sort -u >> requirements-build.in || true

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
