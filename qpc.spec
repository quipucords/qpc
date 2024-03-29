%global __python3 /usr/bin/python3.11
%global python3_pkgversion 3.11
Name:           qpc
Summary:        command-line client interface for quipucords

Version:        1.6.0
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
* Tue Mar 26 2024 Brad Smith <brasmith@redhat.com> - 0:1.6.0-1
- Optimize "clear --all" commands by using new bulk delete APIs.

* Mon Feb 12 2024 Brad Smith <brasmith@redhat.com> - 0:1.5.1-1
- Minor updates and cleanup.

* Mon Jan 22 2024 Brad Smith <brasmith@redhat.com> - 0:1.5.0-1
- Initial release of qpc CLI as an RPM.
