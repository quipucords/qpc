%global python3_pkgversion 3.11
Name:           qpc
Summary:        command-line client interface for quipucords

Version:        1.5.0a1
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
Requires:       python%{python3_pkgversion}-packaging
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
* Thu Oct 12 2023 Brad Smith <brasmith@redhat.com> - 0:1.5.0a1-1
- Initial prototype RPM for upcoming 1.5.0 release series.
