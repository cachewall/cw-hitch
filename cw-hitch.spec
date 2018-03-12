%if 0%{?_no_dist}
        %undefine dist
%endif

%define debug_package	%{nil}
%global name		cw-hitch
%global version		1.4.7
%global release		1%{?dist}.cachewall
%global _hitch_user	varnish
%global _hitch_group	varnish
%global _openssl_prefix /opt/cachewall/cw-openssl
%{!?_pkgdocdir: %global _pkgdocdir %{_docdir}/%{name}-%{version}}

Summary:		Network proxy that terminates TLS/SSL connections
Name:			%{name}
Version:		%{version}
Release:		%{release}
Group:			System Environment/Daemons
License:		BSD
URL:			https://hitch-tls.org/
Provides:		%{name}
BuildRoot:		%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
Source0:		https://hitch-tls.org/source/%{name}-%{version}.tar.gz
BuildRequires:		libev-devel
BuildRequires:		cw-openssl
BuildRequires:		cw-openssl-devel
BuildRequires:		pkgconfig
BuildRequires:		libtool
Requires:		cw-openssl
Requires:		cw-openssl-devel
Patch0:			hitch.systemd.service.patch
Patch1:			hitch.initrc.redhat.patch
Patch2:			hitch-issue-141.patch

%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
Requires(post):		systemd
Requires(preun):	systemd
Requires(postun):	systemd
BuildRequires:		systemd
%else
Requires(preun):	initscripts
%endif

%description
hitch is a network proxy that terminates TLS/SSL connections and forwards the unencrypted traffic to some backend. It is designed to handle 10s of thousands of connections efficiently on multicore machines.

%prep
%setup -q -n %{name}-%{version}
%patch0
%patch1
%patch2

sed -i ' s/^group =.*/group = "nobody"/ ' hitch.conf.example

%build
export RST2MAN=/bin/true

%if 0%{?_openssl_prefix:1}
	export SSL_CFLAGS="-I%{_openssl_prefix}/include -L%{_openssl_prefix}/lib"
	export SSL_LIBS="-lssl"
	export CRYPTO_CFLAGS="-I%{_openssl_prefix}/include -L%{_openssl_prefix}/lib"
	export CRYPTO_LIBS="-lcrypto"
	export C_INCLUDE_PATH="%{_openssl_prefix}/include"
	export LIBRARY_PATH="%{_openssl_prefix}/lib"
%endif

%if 0%{?rhel} == 6
	export CFLAGS="%{optflags} -fPIE"
	export LDFLAGS="-pie"
	export CPPFLAGS="-I%{_includedir}/libev"
%endif

%configure \
	--docdir=%{_pkgdocdir}

%__make %{?_smp_mflags}


%install
%make_install

sed '
	s/user = .*/user = "%{_hitch_user}"/g;
	s/group = .*/group = "%{_hitch_group}"/g;
	s/backend = "\[127.0.0.1\]:8000"/backend = "[127.0.0.1]:6081"/g;
	' hitch.conf.example > hitch.conf

%if 0%{?rhel} == 6
	sed -i 's/daemon = off/daemon = on/g;' hitch.conf
%endif

%__rm -f %{buildroot}%{_pkgdocdir}/hitch.conf.example

%if 0%{?fedora} 
	sed -i 's/^ciphers =.*/ciphers = "PROFILE=SYSTEM"/g' hitch.conf
%endif

%__install -p -D -m 0644 hitch.conf %{buildroot}%{_sysconfdir}/hitch/hitch.conf
%__install -d -m 0755 %{buildroot}%{_sharedstatedir}/hitch
%__install -d -m 0755 %{buildroot}%{_sharedstatedir}/hitch

%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
	%__install -p -D -m 0644 hitch.service %{buildroot}%{_unitdir}/hitch.service
%else
	%__install -p -D -m 0755 hitch.initrc.redhat %{buildroot}%{_initrddir}/hitch
	%__install -d -m 0755 %{buildroot}%{_localstatedir}/run/hitch
%endif


%pre
groupadd -r %{hitch_group} &>/dev/null ||:
useradd -r -g %{hitch_group} -s /sbin/nologin -d %{_sharedstatedir}/hitch %{hitch_user} &>/dev/null ||:

%if 0%{?rhel} == 6
	# Save init.d/hitch if Cachewall.
	[ -f "%{_initrddir}/hitch" ] \
		&& grep -qsi cachewall "%{_initrddir}/hitch" \
		&& %__cp -f %{_initrddir}/hitch %{_initrddir}/.hitch.cachewall ||:
%endif


%post
%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
	%systemd_post hitch.service
%else
	[ -f "%{_initrddir}/.hitch.cachewall" ] \
		&& %__cp -f "%{_initrddir}/.hitch.cachewall" "%{_initrddir}/hitch" ||:

	/sbin/chkconfig --add hitch
%endif


%preun
%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
	%systemd_preun hitch.service
%else
	if [ "$1" -eq 0 ]
	then
		/sbin/service hitch status \
			&& /sbin/service hitch stop &>/dev/null ||:
		/sbin/chkconfig --del hitch ||:
	fi
%endif

%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
%postun
%systemd_postun_with_restart hitch.service
%endif

%files
%doc README.md
%doc CHANGES.rst
%doc hitch.conf.example
%doc docs/*

%{_sbindir}/%{name}
%{_mandir}/man5/%{name}.conf.5*
%{_mandir}/man8/%{name}.8*
%dir %{_sysconfdir}/%{name}
%attr(0700,%hitch_user,%hitch_user) %dir %{_sharedstatedir}/hitch
%config(noreplace) %{_sysconfdir}/%{name}/%{name}.conf

%if 0%{?rhel} == 6
%doc LICENSE
%else
%license LICENSE
%endif

%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
%{_unitdir}/%{name}.service
%ghost %verify(not md5 size mtime)  /run/%{name}/%{name}.pid
%else
%{_initrddir}/%{name}
%attr(0755,%hitch_user,%hitch_user) %dir %{_localstatedir}/run/%{name}
%attr(0644,%hitch_user,%hitch_user) %ghost %verify(not md5 size mtime)  %{_localstatedir}/run/%{name}/%{name}.pid
%endif

%changelog
* Sun Mar 11 2018 Bryon Elston <bryon@cachewall.com> - 1.4.7-1.cachewall
- Updated to upstream release 1.4.7
- Patch for upstream bug #141

* Wed Jun 07 2017 Ingvar Hagelund <ingvar@redpill-linpro.com> - 1.4.6-1
- New upstream release
- Removed unnecessary fix for upstream bug #181

* Wed May 31 2017 Ingvar Hagelund <ingvar@redpill-linpro.com> - 1.4.5-1
- New upstream release
- Had to add -Wno-error=strict-aliasing because of upstream bug #181

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 1.4.4-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Fri Dec 23 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.4.4-2
- More macros
- Use systemd's RuntimeDirectory instead of tmpfilesd
- hitch now owns its homedir, closing bz #1405948

* Thu Dec 22 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.4.4-1
- New upstream release
- Removed merged patch for openssl-1.1

* Thu Nov 17 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.4.3-1
- New upstream release
- Added upstream patch for openssl-1.1

* Thu Nov 17 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.4.2-1
- New upstream release
- Added new manpage for hitch.conf
- Updated sed edit of the example config to match values in the test suite
- Added a hack for un-fedora-styling _pkgdocdir on rhel7 builders

* Sat Sep 24 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.4.1-1
- New upstream release

* Tue Sep 13 2016 Ingvar Hagelund <ingvar@repdill-linpro.com> 1.4.0-1
- New upstream release

* Thu Aug 25 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.3.1-1
- New upstream release
- Fixes for beta3 ironed out upstream, so removed

* Mon Aug 08 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.3.0-0.1.beta3
- New upstream beta release
- Manually build man page, BuildRequires python-docutils => 0.6
- Check suit now runs on el6 without patching

* Fri May 20 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.2.0-2
- Added missing check on upgrade/uninstall in postun script on epel6

* Mon Apr 25 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.2.0-1
- New upstream release
- Clean up test tree before build
- Removed no longer needed test patch 
- Rebased missing_curl_resolve_on_el6 test patch
- Added reload option to systemd service file and sysv initrc script
- Changed the default cipher to "PROFILE=SYSTEM" on fedora

* Wed Feb 03 2016 Fedora Release Engineering <releng@fedoraproject.org> - 1.1.1-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_24_Mass_Rebuild

* Thu Jan 28 2016 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.1.1-1
- New upstream release
- Removed patches included upstream
- No need to rebuild the manpage, as the upstream distribution includes it

* Mon Nov 23 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.1.0-1
- New upstream release
- Use the _pkgdocdir macro to avoid docdir hacks for el6
- Added a patch from upstream that sets stronger ciphers as default

* Thu Oct 15 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.1-1
- New upstream release
- New Home and Source0 URLs
- Rebased patches
- Changed initrc and systemd start up scripts to match new binary name

* Tue Aug 04 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.5.1.beta5
- New upstream beta
- Dropped patch3 and patch5, they are fixed in upstream
- Rebased patch for curl on el6
- hitch no longer autocreates the default config, so use the provided example

* Tue Aug 04 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.4.3.beta4
- Much simpler patch for github issue #37

* Mon Aug 03 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.4.2.beta4
- Patching around upstream github issue #37

* Mon Aug 03 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.4.1.beta4
- New upstream beta
- Dropped setgroups patch as it has been accepted upstream
- Simple sed replace nobody for nogroup in test08

* Sun Jul 19 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.3.4.beta3
- Some more fixes for the fedora package review, ref Cicku

* Thu Jul 16 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.3.3.beta3
- Some more fixes for the fedora package review, ref Jeff Backus

* Fri Jun 26 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.3.2.beta3
- Added _hardened_build macro and PIE on el6

* Thu Jun 25 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.3.1.beta3
- Some fixes for the fedora package review, ref Sören Möller
- Now runs the test suite in check, adding BuildRequire openssl
- Added a patch that fixed missing cleaning running daemons from test suite
- Added a patch that made test07 run on older curl (epel6)
- Package owns /etc/hitch
- Added pidfile to systemd and tmpfiles.d configuration
- Added pidfile to redhat sysv init script

* Wed Jun 10 2015 Ingvar Hagelund <ingvar@redpill-linpro.com> 1.0.0-0.3.beta3
- Initial wrap for fedora
