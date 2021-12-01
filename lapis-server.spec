Name:           lapis-server
Version:        0.1.3
Release:        1%{?dist}
Summary:        Server for the Lapis Build System

License:        MIT
Source0:        https://gitlab.ultramarine-linux.org/lapis/lapis-backend/-/archive/%{version}/lapis-backend-%{version}.tar.gz

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
%autosetup -n lapis-backend-%{version}


%install
rm -rf $RPM_BUILD_ROOT
mkdir -p %{buildroot}%{_localstatedir}/www/lapis
mkdir -p %{buildroot}%{python3_sitelib}
mkdir -p %{buildroot}%{_bindir}
install lapis-server.py -m 755 %{buildroot}%{_bindir}/lapis-server
cp -vr lapis/ %{buildroot}%{python3_sitelib}
install lapis.wsgi -m 644 %{buildroot}%{_localstatedir}/www/lapis/lapis.wsgi


# Apache configuration
mkdir -p %{buildroot}%{_sysconfdir}/httpd/conf.d/
cat > %{buildroot}%{_sysconfdir}/httpd/conf.d/lapis.conf << EOF

<VirtualHost *:80>
    ServerName lapis.example.com

    WSGIDaemonProcess lapis user=apache group=apache threads=5
    WSGIScriptAlias /lapis /var/www/lapis/lapis.wsgi

    <Directory /var/www/lapis>
        WSGIProcessGroup lapis
        WSGIApplicationGroup %{GLOBAL}
        Order deny,allow
        Require all granted
    </Directory>
RewriteEngine on
RewriteCond %{SERVER_NAME} =lapis.example.com
RewriteRule ^ https://%{SERVER_NAME}%{REQUEST_URI} [END,NE,R=permanent]
</VirtualHost>
EOF



%files
%doc README.md

%{_bindir}/lapis-server
%{python3_sitelib}/lapis/
%{_localstatedir}/www/lapis/lapis.wsgi
%{_sysconfdir}/httpd/conf.d/lapis.conf
%changelog
* Fri Nov 26 2021 Cappy Ishihara <cappy@cappuchino.xyz> - 0.1.2-1.um35
- Added Apache configuration
- Modified default endpoint to /lapis
- Hotfix of SQL schema initialization
- Now no longer downloads the main branch of the repository
* Fri Nov 26 2021 Cappy Ishihara <cappy@cappuchino.xyz>
- Initial Release
