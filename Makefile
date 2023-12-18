DATE		= $(shell date)
PYTHON		= $(shell poetry run which python 2>/dev/null || which python)
PKG_VERSION = $(shell poetry -s version)
BUILD_DATE  = $(shell date +'%B %d, %Y')
PARALLEL_NUM ?= $(shell python -c 'import multiprocessing as m;print(int(max(m.cpu_count()/2, 2)))')
QPC_VAR_PROGRAM_NAME := $(or $(QPC_VAR_PROGRAM_NAME), qpc)
QPC_VAR_PROGRAM_NAME_UPPER := $(shell echo $(QPC_VAR_PROGRAM_NAME) | tr '[:lower:]' '[:upper:]')
QPC_VAR_CURRENT_YEAR := $(shell date +'%Y')
QPC_VAR_PROJECT := $(or $(QPC_VAR_PROJECT), Quipucords)
OLD_MAN_PAGE_BUILD_DATE := $(shell grep -e "^\.TH" docs/_build/qpc.1 | cut -d '"' -f 6)

TOPDIR = $(shell pwd)
DIRS	= test bin locale src
PYDIRS	= quipucords
BINDIR  = bin

SPHINX_BUILD = $(shell poetry run which sphinx-build)
SED = sed

help:
	@echo "Please use \`make <target>' where <target> is one of:"
	@echo "  help                to show this message"
	@echo "  install             to install the client egg"
	@echo "  clean               to remove cache, dist, build, and egg files"
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
	find . -type f -name '*.pyc' -delete
	find . -type d -name __pycache__ -delete

install:
	$(PYTHON) setup.py build -f
	$(PYTHON) setup.py install -f

lint: lint-ruff lint-black lint-docs

lint-ruff:
	poetry run ruff .

lint-black:
	poetry run black --diff --check .

lint-docs:
	poetry run rstcheck docs/source/man-template.rst
	poetry run rstcheck docs/_build/man-qpc.rst

test:
	poetry run pytest

test-coverage:
	poetry run pytest --cov=qpc
	poetry run coverage report --show-missing
	poetry run coverage xml

# write a man page (roff format) with placeholders for names, version, and dates
update-man-template-roff:
	@$(SPHINX_BUILD) -b man -q \
	  -D project='QPC_VAR_PROGRAM_NAME' \
	  -D release='PKG_VERSION' \
	  -D today='BUILD_DATE' \
	  docs docs/_build

# generate an upstream "qpc" man page in human-readable RST
generate-man-qpc-rst:
	@$(SED) \
	  -e "s/QPC_VAR_PROGRAM_NAME/${QPC_VAR_PROGRAM_NAME}/g" \
	  -e "s/QPC_VAR_PROJECT/${QPC_VAR_PROJECT}/g" \
	  -e "s/QPC_VAR_CURRENT_YEAR/${QPC_VAR_CURRENT_YEAR}/g" \
	  docs/source/man-template.rst

update-man-qpc-rst:
	$(MAKE) --no-print-directory generate-man-qpc-rst > docs/_build/man-qpc.rst

# generate an upstream "qpc" man page in man-parsable roff format
generate-man-qpc-roff:
	@$(SED) \
	  -e "s/QPC_VAR_PROGRAM_NAME/${QPC_VAR_PROGRAM_NAME}/g" \
	  -e "s/QPC_VAR_PROJECT/${QPC_VAR_PROJECT}/g" \
	  -e "s/QPC_VAR_CURRENT_YEAR/${QPC_VAR_CURRENT_YEAR}/g" \
	  -e "s/PKG_VERSION/${PKG_VERSION}/g" \
	  -e "s/BUILD_DATE/${BUILD_DATE}/g" \
	  docs/_build/QPC_VAR_PROGRAM_NAME.1

update-man-qpc-roff:
	$(MAKE) --no-print-directory generate-man-qpc-roff > docs/_build/qpc.1

# regenerate and update all man page files
manpage:
	$(MAKE) update-man-template-roff
	$(MAKE) update-man-qpc-rst
	$(MAKE) update-man-qpc-roff

# test if man page files have changed
manpage-test:
	$(MAKE) update-man-template-roff
	$(MAKE) update-man-qpc-rst
	$(MAKE) update-man-qpc-roff BUILD_DATE="${OLD_MAN_PAGE_BUILD_DATE}"
	git diff --exit-code docs
	git diff --staged --exit-code docs

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
