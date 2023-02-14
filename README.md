[![GitHub license](https://img.shields.io/github/license/quipucords/qpc.svg)](https://github.com/quipucords/qpc/blob/master/LICENSE)
[![Build Status](https://travis-ci.org/quipucords/qpc.svg?branch=master)](https://travis-ci.org/quipucords/qpc)
[![Code Coverage](https://codecov.io/gh/quipucords/qpc/branch/master/graph/badge.svg)](https://codecov.io/gh/quipucords/qpc)
[![Documentation Status](https://readthedocs.org/projects/qpc/badge/)](https://qpc.readthedocs.io/en/latest/)
[![COPR Status](https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/package/qpc/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/g/quipucords/qpc/package/qpc/)
[![Updates](https://pyup.io/repos/github/quipucords/qpc/shield.svg)](https://pyup.io/repos/github/quipucords/qpc/)
[![Python 3](https://pyup.io/repos/github/quipucords/qpc/python-3-shield.svg)](https://pyup.io/repos/github/quipucords/qpc/)


# qpc - RPM command line tool for quipucords
qpc is the RPM command line tool for quipucords. To learn more about quipucords visit [qpc man page](docs/source/man.rst).

# Overview
This *README* file contains information about the installation and development of qpc, as well as instructions about where to find basic usage, known issues, and best practices information.

- [Installation](#installation)
- [Command Syntax and Usage](#commands)
- [Development](#development)
- [Issues](#issues)
- [Authors](#authors)
- [Contributing](#contributing)
- [Copyright and License](#copyright)

## Requirements and Assumptions
Before installing qpc on a system, review the following guidelines about installing and running qpc:

 * qpc is written to run on RHEL or Fedora servers.
 * The system that qpc is installed on must have access to the systems to be discovered and inspected.
 * The target systems must be running SSH.
 * The user account that qpc uses for the SSH connection into the target systems must have adequate permissions to run commands and read certain files, such as privilege escalation required for the `systemctl` command.
 * The user account that qpc uses for a machine requires an sh shell or a similar shell. For example, the shell *cannot* be a /sbin/nologin or /bin/false shell.

The Python packages that are required for running qpc on a system can be found in the `pyyproject.toml` and `poetry.lock` file under "main" group. Development packages are under "dev" group.

#  <a name="installation"></a> Installation
```
dnf copr enable @quipucords/qpc 
dnf install qpc
```

# <a name="commands"></a> Command Syntax and Usage
The complete list of options for each qpc command and subcommand are listed in the qpc man page. The man page information also contains usage examples and some best practice recommendations.

For expanded information on credential entries, sources, scanning, and output, see the [syntax and usage document](./docs/source/man.rst).

# <a name="development"></a> Development
To work with the qpc code, begin by cloning the repository:
```
git clone git@github.com:quipucords/qpc.git
```

qpc currently supports Python 3.6. If you do not have Python on your system, follow these [instructions](https://www.python.org/downloads/>).


## Installation with development dependencies

This project uses poetry to manage python dependencies and virtual environment. Having
poetry installed, just run the following to install the project:

```
poetry install
```

## Linting
To lint changes that are made to the source code, run the following command::
```
make lint
```

## Unit Testing
To run the unit tests, use the following command::
```
make test
```

# <a name="issues"></a> Issues
To report bugs for qpc [open issues](https://github.com/quipucords/qpc/issues) against this repository in Github. Complete the issue template when opening a new bug to improve investigation and resolution time.


# <a name="authors"></a> Authors
Authorship and current maintainer information can be found in [AUTHORS](AUTHORS.md).


# <a name="contributing"></a> Contributing
See the [CONTRIBUTING](CONTRIBUTING.md) guide for information about contributing to the project.


# <a name="copyright"></a> Copyright and License
Copyright 2017-2019, Red Hat, Inc.

quipucords is released under the [GNU Public License version 3](LICENSE)

