%global __python3 /usr/bin/python3.12
%global python3_pkgversion 3.12
Name:           qpc
Summary:        command-line client interface for quipucords

Version:        1.9.0
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

%description
qpc is the command-line client interface for the quipucords server.

%prep
%autosetup -n qpc-%{version}

%build
%py3_build

%install
QPC_VAR_PROGRAM_NAME=qpc %py3_install
mkdir -p %{buildroot}%{_mandir}/man1/
sed \
  -e "s/QPC_VAR_PROGRAM_NAME/qpc/g" \
  -e "s/QPC_VAR_PROJECT/quipucords/g" \
  -e "s/QPC_VAR_CURRENT_YEAR/$(date +'%Y')/g" \
  -e "s/BUILD_DATE/$(date +'%B %d, %Y')/g" \
  docs/_build/QPC_VAR_PROGRAM_NAME.1 > \
  %{buildroot}%{_mandir}/man1/qpc.1

%files
%license LICENSE
%doc README.md
%doc %{_mandir}/man1/qpc.*
%{_bindir}/qpc
%{python3_sitelib}/qpc/
%{python3_sitelib}/qpc-*.egg-info/

%changelog
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
