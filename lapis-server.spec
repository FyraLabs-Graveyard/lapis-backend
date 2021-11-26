Name:           lapis-server
Version:        0.1
Release:        1%{?dist}
Summary:        Server for the Lapis Build System

License:        MIT
Source0:        https://gitlab.ultramarine-linux.org/lapis/lapis-backend/-/archive/main/lapis-backend-main.tar.gz

BuildRequires:  python3-devel
Requires:       python3-flask
Requires:       python3
Requires:       python3-setuptools
Requires:       python3-GitPython
Requires:       mock
Requires:       createrepo
Requires:       python3-rpm
Requires:       python3-psycopg2

%description


%prep
%autosetup -n lapis-backend-main


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p %{buildroot}%{_localstatedir}/www/lapis
mkdir -p %{buildroot}%{python3_sitelib}
mkdir -p %{buildroot}%{_bindir}
install lapis-server.py -m 755 %{buildroot}%{_bindir}/lapis-server
cp -vr lapis/ %{buildroot}%{python3_sitelib}
install lapis.wsgi -m 644 %{buildroot}%{_localstatedir}/www/lapis/lapis.wsgi

%files
%doc README.md

%{_bindir}/lapis-server
%{python3_sitelib}/lapis/
%{_localstatedir}/www/lapis/lapis.wsgi
%changelog
* Fri Nov 26 2021 Cappy Ishihara <cappy@cappuchino.xyz>
- Initial Release
