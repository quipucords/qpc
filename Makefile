DATE		= $(shell date)
PYTHON		= $(shell which python)

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
	@echo "  lint-isort          to run the isort import order checker"
	@echo "  lint-flake8         to run the flake8 linter"
	@echo "  lint-black          to run the black format checker"
	@echo "  lint-docs           to run rstcheck against docs"
	@echo "  test                to run unit tests"
	@echo "  test-coverage       to run unit tests and measure test coverage"
	@echo "  manpage             to build the manpage"
	@echo "  insights-client     to setup the insights-client egg"
	@echo "  insights-clean      to remove the insights-client egg"

clean:
	-rm -rf dist/ build/ qpc.egg-info/

install:
	$(PYTHON) setup.py build -f
	$(PYTHON) setup.py install -f

lint:
	tox -e lint

lint-isort:
	tox -e lint-isort

lint-flake8:
	tox -e lint-flake8

lint-black:
	tox -e lint-black

lint-docs:
	poetry run rstcheck docs/source/man.rst

test:
	tox -e py39

test-coverage:
	coverage run -m unittest discover qpc/ -v
	coverage report -m --omit $(OMIT_PATTERNS)
	echo $(OMIT_PATTERNS)

manpage:
	$(pandoc) docs/source/man.rst \
	  --standalone -t man -o docs/qpc.1 \
	  --variable=section:1 \
	  --variable=date:'June 6, 2019' \
	  --variable=footer:'version 3' \
	  --variable=header:'QPC Command Line Guide'

insights-client:
	cd ../insights-client;sudo sh lay-the-eggs-osx.sh
	curl https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg.asc > last_stable.egg.asc
	sudo mv last_stable.egg.asc /var/lib/insights/last_stable.egg.asc
	curl https://api.access.redhat.com/r/insights/v1/static/core/insights-core.egg > last_stable.egg
	sudo mv last_stable.egg /var/lib/insights/last_stable.egg


insights-clean:
	sudo rm -rf /etc/insights-client/*
	sudo rm -rf /var/lib/insights/*
