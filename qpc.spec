%if 0%{?fedora} >= 41
    # Fedora 41 with Python 3.13
    # When will RHEL have 3.13? TBD
    # Add condition like this when necessary:
    # || 0%{?rhel} >= 11
    %global python3_pkgversion 3.13
    %global __python3 /usr/bin/python3.13
%else
    # older distros with Python 3.12
    %global python3_pkgversion 3.12
    %global __python3 /usr/bin/python3.12
%endif
%global binname qpc

Name:           qpc
Summary:        command-line client interface for quipucords

Version:        2.4.1
Release:        1%{?dist}
Epoch:          0

License:        GPLv3
URL:            https://github.com/quipucords/qpc
Source0:        %{url}/archive/%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python%{python3_pkgversion}-devel
BuildRequires:  python%{python3_pkgversion}-setuptools

Requires:       python%{python3_pkgversion}
Requires:       python%{python3_pkgversion}-cryptography
Requires:       python%{python3_pkgversion}-requests
Requires:       python%{python3_pkgversion}-setuptools
# Note: autosetup may dynamically add some "Requires" from pyproject.toml.

%description
qpc is the command-line client interface for the quipucords server.

%prep
%autosetup -n qpc-%{version}

%build
sed -i \
  -e 's/^QPC_VAR_PROGRAM_NAME = os.environ.get("QPC_VAR_PROGRAM_NAME", "qpc")/QPC_VAR_PROGRAM_NAME = os.environ.get("QPC_VAR_PROGRAM_NAME", "%{binname}")/' \
  %{_builddir}/qpc-%{version}/qpc/release.py
sed -i \
  -e 's/^qpc = "qpc.__main__:main"$/%{binname} = "qpc.__main__:main"/' \
  %{_builddir}/qpc-%{version}/pyproject.toml
%py3_build

%install
QPC_VAR_PROGRAM_NAME=%{binname} %py3_install
mkdir -p %{buildroot}%{_mandir}/man1/
sed \
  -e "s/QPC_VAR_PROGRAM_NAME/%{binname}/g" \
  -e "s/QPC_VAR_PROJECT/quipucords/g" \
  -e "s/QPC_VAR_CURRENT_YEAR/$(date +'%Y')/g" \
  -e "s/BUILD_DATE/$(date +'%B %d, %Y')/g" \
  docs/_build/QPC_VAR_PROGRAM_NAME.1 > \
  %{buildroot}%{_mandir}/man1/%{binname}.1

%files
%license LICENSE
%doc README.md
%doc %{_mandir}/man1/%{binname}.*
%{_bindir}/%{binname}
%{python3_sitelib}/qpc/
%{python3_sitelib}/qpc-*.egg-info/

%changelog
* Fri Apr 4 2025 Brad Smith <brasmith@redhat.com> - 0:1.13.1-1
- Pattern replace build bin name more consistently.

* Fri Jan 3 2025 Brad Smith <brasmith@redhat.com> - 0:1.12.0-1
- Support python 3.13 on fedora >= 41

* Mon Jul 15 2024 Brad Smith <brasmith@redhat.com> - 0:1.8.2-1
- Better output and exit code from incomplete commands.
- Minor performance updates and cleanup.

* Tue Jun 11 2024 Bruno Ciconelle <bciconel@redhat.com> - 0:1.8.1-1
- Add support for aggregate report (Brad Smith)
- Upgrade python version to 3.12

* Mon May 13 2024 Bruno Ciconelle <bciconel@redhat.com> - 0:1.8.0-1
- Drop support to Decision Manager (BRMS).
- Refactor report upload to use the async view.
- Optimize report merge.
- Deprecate report merge-status; scan job should be used instead.

* Fri Apr 26 2024 Brad Smith <brasmith@redhat.com> - 0:1.7.0-1
- Improve user experience with paginated results.

* Tue Mar 26 2024 Brad Smith <brasmith@redhat.com> - 0:1.6.0-1
- Optimize "clear --all" commands by using new bulk delete APIs.

* Mon Feb 12 2024 Brad Smith <brasmith@redhat.com> - 0:1.5.1-1
- Minor updates and cleanup.

* Mon Jan 22 2024 Brad Smith <brasmith@redhat.com> - 0:1.5.0-1
- Initial release of qpc CLI as an RPM.
