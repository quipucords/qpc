.. image:: https://travis-ci.org/quipucords/qpc.svg?branch=master
    :target: https://travis-ci.org/quipucords/qpc
.. image:: https://codecov.io/gh/quipucords/qpc/branch/master/graph/badge.svg
  :target: https://codecov.io/gh/quipucords/qpc
.. image:: https://requires.io/github/quipucords/qpc/requirements.svg?branch=master
    :target: https://requires.io/github/quipucords/qpc/requirements/?branch=master
    :alt: Requirements Status
.. image:: https://readthedocs.org/projects/quipucords/badge/?version=latest
    :alt: Documentation Status
    :scale: 100%
    :target: https://quipucords.readthedocs.io/en/latest/?badge=latest
.. image:: https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/package/qpc/status_image/last_build.png
    :alt: CLI RPM Build Status
    :scale: 100%
    :target: https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/

qpc - RPM command line tool for quipucords
==========================================

qpc is the RPM command line tool for quipucords. To learn more about quipucords visit the `GitHub page <https://github.com/quipucords/quipucords/>`_. Documentation for qpc is available through `readthedocs <https://qpc.readthedocs.io/en/latest/`_.


This *README* file contains information about the installation and development of qpc, as well as instructions about where to find basic usage, known issues, and best practices information.

- `Requirements and Assumptions`_
- `Installation`_
- `Command Syntax and Usage`_
- `Development`_
- `Issues`_
- `Authors`_
- `Contributing`_
- `Copyright and License`_

Requirements and Assumptions
----------------------------
Before installing qpc on a system, review the following guidelines about installing and running qpc:

 * qpc is written to run on RHEL or Fedora servers.
 * The system that qpc is installed on must have access to the systems to be discovered and inspected.
 * The target systems must be running SSH.
 * The user account that qpc uses for the SSH connection into the target systems must have adequate permissions to run commands and read certain files, such as privilege escalation required for the ``systemctl`` command.
 * The user account that qpc uses for a machine requires an sh shell or a similar shell. For example, the shell *cannot* be a /sbin/nologin or /bin/false shell.

The Python packages that are required for running qpc on a system can be found in the ``dev-requirements.txt`` file. The Python packages that are required to build and test qpc from source can be found in the ``requirements.txt`` and ``dev-requirements.txt`` files.

Installation
------------
The following information contains instructions for installing qpc.

Command Line
^^^^^^^^^^^^
To install QPC on RHEL 6 or CentOS 6 run::

    yum install https://github.com/quipucords/qpc/releases/latest/download/qpc.el6.noarch.rpm

To install QPC on RHEL 7 or CentOS 7 run::

    yum install https://github.com/quipucords/qpc/releases/latest/download/qpc.el7.noarch.rpm

Command Syntax and Usage
------------------------
The complete list of options for each qpc command and subcommand are listed in the qpc man page. The man page information also contains usage examples and some best practice recommendations.

For expanded information on credential entries, sources, scanning, and output, see the `syntax and usage document <docs/source/man.rst>`_.

Development
-----------
To work with the qpc code, begin by cloning the repository::

    git clone git@github.com:quipucords/qpc.git

qpc currently supports Python 3.4, 3.5 and 3.6. If you do not have Python on your system, follow these `instructions <https://www.python.org/downloads/>`_.


Setting Up a Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Developing inside a virtual environment is recommended. Add desired environment variables to the `.env` file before creating your virtual environment.  You can copy ``.env.example`` to get started.

On Mac run the following command to set up a virtual environment::

    brew install pipenv
    pipenv shell
    pip install -r dev-requirements.txt

On Linux run the following command to set up a virtual environment::

    sudo yum install python-tools (or dnf for Fedora)
    pip3 install pipenv
    pipenv shell
    pip install -r dev-requirements.txt


Developing with Insights Client
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
Information on installing and developing with the insights client can be found in `Insights Configuration <insights_configuration.rst>`_.


Linting
^^^^^^^
To lint changes that are made to the source code, run the following command::

    make lint

Testing
^^^^^^^

Unit Testing
""""""""""""

To run the unit tests, use the following command::

    make test


Issues
------
To report bugs for qpc `open issues <https://github.com/quipucords/qpc/issues>`_ against this repository in Github. Complete the issue template when opening a new bug to improve investigation and resolution time.


Authors
-------
Authorship and current maintainer information can be found in `AUTHORS <AUTHORS.rst>`_.


Contributing
------------
See the `CONTRIBUTING <CONTRIBUTING.rst>`_ guide for information about contributing to the project.


Copyright and License
---------------------
Copyright 2017-2019, Red Hat, Inc.

quipucords is released under the `GNU Public License version 3 <LICENSE>`_

