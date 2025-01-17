%global debug_package   %{nil}

# container-selinux
%global git0 https://github.com/projectatomic/container-selinux
%global commit0 988431700370bf7f554ab6507c836a9aa19e47ff
%global shortcommit0 %(c=%{commit0}; echo ${c:0:7})

# container-selinux stuff (prefix with ds_ for version/release etc.)
# Some bits borrowed from the openstack-selinux package
%global selinuxtype targeted
%global moduletype services
%global modulenames container

# Usage: _format var format
# Expand 'modulenames' into various formats as needed
# Format must contain '$x' somewhere to do anything useful
%global _format() export %1=""; for x in %{modulenames}; do %1+=%2; %1+=" "; done;

# Relabel files
%global relabel_files() %{_sbindir}/restorecon -R %{_bindir}/*podman* %{_bindir}/*runc* %{_bindir}/*crio %{_bindir}/docker* %{_localstatedir}/run/containerd.sock %{_localstatedir}/run/docker.sock %{_localstatedir}/run/docker.pid %{_sysconfdir}/docker %{_sysconfdir}/crio %{_localstatedir}/log/docker %{_localstatedir}/log/lxc %{_localstatedir}/lock/lxc %{_unitdir}/docker.service %{_unitdir}/docker-containerd.service %{_unitdir}/docker-latest.service %{_unitdir}/docker-latest-containerd.service %{_sysconfdir}/docker %{_libexecdir}/docker* &> /dev/null || :

# Version of SELinux we were using
%global selinux_policyver 3.13.1-220

%define epoch 2

Name: container-selinux
Epoch: 2
Version: 2.138
Release: 5
License: GPLv2
URL: %{git0}
Summary: SELinux policies for container runtimes
Source0: %{git0}/archive/%{commit0}/%{name}-%{shortcommit0}.tar.gz
BuildArch: noarch
Patch1: 0001-systemd_dbus_chat_resolved-has-been-deprecated-use-s.patch
BuildRequires: pkgconfig(systemd)
BuildRequires: selinux-policy >= %{selinux_policyver}
BuildRequires: selinux-policy-devel >= %{selinux_policyver}
# RE: rhbz#1195804 - ensure min NVR for selinux-policy
Requires: selinux-policy >= %{selinux_policyver}
Requires(post): selinux-policy-base >= %{selinux_policyver}
Requires(post): selinux-policy-targeted >= %{selinux_policyver}
Requires(post): policycoreutils
Requires(post): libselinux-utils
Requires(post): sed
Obsoletes: %{name} <= 2:1.12.5-13
Obsoletes: docker-selinux <= 2:1.12.4-28
Provides: docker-selinux = %{epoch}:%{version}-%{release}

%description
SELinux policy modules for use with container runtimes.

%prep
%autosetup -n %{name}-%{commit0} -p1

%build
make

%install
# install policy modules
%_format MODULES $x.pp.bz2
install -d %{buildroot}%{_datadir}/selinux/packages
install -d -p %{buildroot}%{_datadir}/selinux/devel/include/services
install -p -m 644 container.if %{buildroot}%{_datadir}/selinux/devel/include/services
install -m 0644 $MODULES %{buildroot}%{_datadir}/selinux/packages

# remove spec file
rm -rf container-selinux.spec

%check

%post
# Install all modules in a single transaction
if [ $1 -eq 1 ]; then
    %{_sbindir}/setsebool -P -N virt_use_nfs=1 virt_sandbox_use_all_caps=1
fi
%_format MODULES %{_datadir}/selinux/packages/$x.pp.bz2
%{_sbindir}/semodule -n -s %{selinuxtype} -r container 2> /dev/null
%{_sbindir}/semodule -n -s %{selinuxtype} -d docker 2> /dev/null
%{_sbindir}/semodule -n -s %{selinuxtype} -d gear 2> /dev/null
%{_sbindir}/semodule -n -X 200 -s %{selinuxtype} -i $MODULES > /dev/null
if %{_sbindir}/selinuxenabled ; then
    %{_sbindir}/load_policy
    %relabel_files
    if [ $1 -eq 1 ]; then
	restorecon -R %{_sharedstatedir}/docker &> /dev/null || :
	restorecon -R %{_sharedstatedir}/containers &> /dev/null || :
    fi
fi
. %{_sysconfdir}/selinux/config
sed -e "\|container_file_t|h; \${x;s|container_file_t||;{g;t};a\\" -e "container_file_t" -e "}" -i /etc/selinux/${SELINUXTYPE}/contexts/customizable_types 
matchpathcon -qV %{_sharedstatedir}/containers || restorecon -R %{_sharedstatedir}/containers &> /dev/null || :


%postun
if [ $1 -eq 0 ]; then
%{_sbindir}/semodule -n -r %{modulenames} docker &> /dev/null || :
if %{_sbindir}/selinuxenabled ; then
%{_sbindir}/load_policy
%relabel_files
fi
fi

#define license tag if not already defined
%{!?_licensedir:%global license %doc}

%files
%doc README.md
%{_datadir}/selinux/*

%changelog
* Tue Oct 26 2021 caodongxia <caodongxia@huawei.com> - 2.138-5
- DESC: systemd_dbus_chat_resolved has been deprecated, use systemd_chat_resolved instead

* Wed Aug 11 2021 chenyanpanHW <chenyanpan@huawei.com> - 2.138-4
- DESC: delete -Sgit from %autosetup, and delete BuildRequires git

* Mon Dec 14 2020 openEuler Buildteam <buildteam@openeuler.org> - 2.138-2
- Update container-selinux spec

* Wed Aug 19 2020 openEuler Buildteam <buildteam@openeuler.org> - 2.138-1
- Update container-selinux to v2.138.1

* Sat Sep 14 2019 openEuler Buildteam <buildteam@openeuler.org> - 2.73-3
- Package init
