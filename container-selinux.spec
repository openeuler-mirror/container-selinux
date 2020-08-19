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
Version: 2.138.0
Release: 1
License: GPLv2
URL: %{git0}
Summary: SELinux policies for container runtimes
Source0: %{git0}/archive/%{commit0}/%{name}-%{shortcommit0}.tar.gz
BuildArch: noarch
BuildRequires: git
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
%autosetup -Sgit -n %{name}-%{commit0}

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
* Tue Sep 01 2020 openEuler Buildteam <buildteam@openeuler.org> - 2.138.0-1
- Update container-selinux to v2.138.0-1

* Sat Sep 14 2019 openEuler Buildteam <buildteam@openeuler.org> - 2.73-3
- Package init

* Sat Sep 22 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.73-2
- Remove requires for policycoreutils-python-utils we don't need it.

* Wed Sep 12 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.73-1
- Define spc_t as a container_domain, so that container_runtime will transition
to spc_t even when setup with nosuid.

* Wed Sep 12 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.72-1
- Allow container_runtimes to setattr on callers fifo_files

* Mon Aug 27 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.71-2
- Fix restorecon to not error on missing directory

* Wed Aug 22 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.71-1
- Allow unconfined_r to transition to system_r over container_runtime_exec_t

* Wed Aug 22 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.70-1
- Allow unconfined_t to transition to container_runtime_t over container_runtime_exec_t

* Wed Jul 25 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.69-1
- dontaudit attempts to write to sysctl_kernel_t

* Wed Jul 18 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.68-2.gitc139a3d
- autobuilt c139a3d

* Mon Jul 16 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.67-1
- Add label for /var/lib/origin
- Add customizable_file_t to customizable_types

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2:2.67-3.dev.git042f7cf
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Mon Jul 09 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.67-2.git042f7cf
- autobuilt 042f7cf

* Sat Jul 07 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.67-1.git0407867
- bump to 2.67
- autobuilt 0407867

* Sat Jun 30 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.66-1
- Allow container runtimes to dbus chat with systemd-resolved

* Tue Jun 12 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.64-1.gitdfaf8fd
- bump to 2.64
- autobuilt dfaf8fd

* Mon Jun 11 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.65-1
- Add new type to handle containers running with a non priv user in a userns
- allow containers to map all sockets

* Sun Jun 3 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.64-1.gitdfaf8fd
- Allow containers to create all socket classes

* Wed May 30 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.63-1
- Allow containers to create icmp packets

* Fri May 25 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.62-1.git1ecf953
- bump to 2.62
- autobuilt 1ecf953

* Mon May 21 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.61-1
- Allow spc_t to load kernel modules from inside of container 

* Mon May 21 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.60-1
- Allow containers to list cgroup directories

* Mon May 21 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.59-1
- Transition for unconfined_service_t to container_runtime_t when executing container_runtime_exec_t.

* Mon May 21 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.58-2
- Run restorecon /usr/bin/podman in postinstall

* Fri May 18 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.58-1
- Add labels to allow podman to be run from a systemd unit file

* Tue Apr 17 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-12.gitd248f91
- autobuilt commit d248f91

* Tue Apr 17 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-11.gitd248f91
- autobuilt commit d248f91

* Mon Apr 16 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-10.gitd248f91
- autobuilt commit d248f91

* Mon Apr 16 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-9.gitd248f91
- autobuilt commit d248f91

* Mon Apr 16 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-8
- autobuilt commit d248f91

* Mon Apr 16 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-7
- autobuilt commit d248f91

* Mon Apr 16 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-6
- autobuilt commit d248f91

* Mon Apr 09 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-5
- autobuilt commit d248f91

* Mon Apr 09 2018 Lokesh Mandvekar (Bot) <lsm5+bot@fedoraproject.org> - 2:2.55-4
- autobuilt commit d248f91

* Mon Apr 09 2018 Lokesh Mandvekar <lsm5@fedoraproject.org> - 2:2.55-3
- autobuilt commit d248f91

* Mon Apr 09 2018 Lokesh Mandvekar <lsm5@fedoraproject.org> - 2:2.55-2
- autobuilt commit d248f91

* Thu Mar 15 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.55-1
- Dontaudit attempts by containers to write to /proc/self

* Wed Mar 14 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.54-1
-  Add rules for container domains to make writing custom policy easier
-  Allow shell_exec_t as a container_runtime_t entrypoint

* Thu Mar 8 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.52-1
- Add rules for container domains to make writing custom policy easier

* Thu Mar 8 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.51-1
- Allow shell_exec_t as a container_runtime_t entrypoint

* Wed Mar 7 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.50-1
- Allow bin_t as a container_runtime_t entrypoint
- Add rules for running container runtimes on mls

* Thu Feb 15 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.48-1
- Allow container domains to map container_file_t directories

* Sat Feb 10 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.47-1
- Change default label of /exports to container_var_lib_t

* Fri Feb 09 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 2:2.46-3
- Escape macros in %%CHANGELOG

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 2:2.46-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Sat Feb 03 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.46-1
- Add support for nosuid_transition flags for container_runtime and unconfined domains
* Fri Feb 02 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.45-1
- Allow containers to sendto their own stream sockets

* Mon Jan 29 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.44-1
- Allow container domains to read kernel ipc info

* Mon Jan 22 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.43-1
- Allow containers to memory map the fifo_files leaked into container from
container runtimes.

* Tue Jan 16 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.42-1
- Allow unconfined domains to transition to container types, when no-new-privs is set.

* Tue Jan 9 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.41-1
- Add support to nnp_transition for container domains
- Eliminates need for typebounds.

* Tue Jan 9 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.40-1
- Allow container_runtime_t to use user ttys
- Fixes bounds check for container_t

* Mon Jan 8 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.39-1
- Allow container runtimes to use interited terminals.  This helps
satisfy the bounds check of container_t versus container_runtime_t.

* Sat Jan 6 2018 Dan Walsh <dwalsh@fedoraproject.org> - 2.38-1
- Allow container runtimes to mmap container_file_t devices
- Add labeling for rhel push plugin

* Tue Dec 12 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.37-1
- Allow containers to use inherited ttys
- Allow ostree to handle labels under /var/lib/containers/ostree

* Mon Nov 27 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.36-1
- Allow containers to relabelto/from all file types to container_file_t

* Mon Nov 27 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.35-1
- Allow container to map chr_files labeled container_file_t

* Wed Nov 22 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.34-1
- Dontaudit container processes getattr on kernel file systems

* Sun Nov 19 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.33-1
- Allow containers to read /etc/resolv.conf and /etc/hosts if volume
- mounted into container.

* Wed Nov 8 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.32-1
- Make sure users creating content in /var/lib with right labels

* Thu Oct 26 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.31-1
- Allow the container runtime to dbus chat with dnsmasq
- add dontaudit rules for container trying to write to /proc

* Tue Oct 10 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.29-1
- Add support for lxcd
- Add support for labeling of tmpfs storage created within a container.

* Mon Oct 9 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.28-1
- Allow a container to umount a container_file_t filesystem

* Fri Sep 22 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.27-1
-  Allow container runtimes to work with the netfilter sockets
-  Allow container_file_t to be an entrypoint for VM's
-  Allow spc_t domains to transition to svirt_t

* Fri Sep 22 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.24-1
-     Make sure container_runtime_t has all access of container_t

* Thu Sep 7 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.23-1
- Allow container runtimes to create sockets in tmp dirs

* Tue Sep 5 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.22-1
- Add additonal support for crio labeling.

* Mon Aug 14 2017 Troy Dawson <tdawson@redhat.com> - 2.21-3
- Fixup spec file conditionals

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 2:2.21-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Thu Jul 6 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.21-1
- Allow containers to execmod on container_share_t files.

* Thu Jul 6 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.20-2
- Relabel runc and crio executables

* Fri Jun 30 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.20-1
- Allow container processes to getsession

* Mon Jun 12 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.19-1
- Allow containers to create tun sockets

* Tue Jun 6 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.18-1
- Fix labeling for CRI-O files in overlay subdirs

* Mon Jun 5 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.17-1
- Revert change to run the container_runtime as ranged

* Thu Jun 1 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.16-1
- Add default labeling for cri-o in /etc/crio directories

* Wed May 31 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.15-1
- Allow container types to read/write container_runtime fifo files
- Allow a container runtime to mount on top of its own /proc

* Fri May 19 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.14-1
- Add labels for crio rename
- Break container_t rules out to use a separate container_domain
- Allow containers to be able to set namespaced SYCTLS
- Allow sandbox containers manage fuse files.
- Fixes to make container_runtimes work on MLS machines
- Bump version to allow handling of container_file_t filesystems
- Allow containers to mount, remount and umount container_file_t file systems
- Fixes to handle cap_userns
- Give container_t access to XFRM sockets
- Allow spc_t to dbus chat with init system
- Allow spc_t to dbus chat with init system
- Add rules to allow container runtimes to run with unconfined disabled
- Add rules to support cgroup file systems mounted into container.
- Fix typebounds entrypoint problems
- Fix typebounds problems
- Add typebounds statement for container_t from container_runtime_t
- We should only label runc not runc*

* Tue Feb 28 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.10-1
- Add rules to allow container runtimes to run with unconfined disabled
- Add rules to support cgroup file systems mounted into container.

* Mon Feb 13 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2.9-1
- Add rules to allow container_runtimes to run with unconfined disabled

* Thu Feb 9 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2:8.1-1
- Allow container_file_t to be stored on cgroup_t file systems

* Tue Feb 7 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2:7.1-1
- Fix type in container interface file

* Mon Feb 6 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2:6.1-1
- Fix typebounds entrypoint problems

* Fri Jan 27 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2:5.1-1
- Fix typebounds problems

* Thu Jan 19 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2:4.1-1
- Add typebounds statement for container_t from container_runtime_t
- We should only label runc not runc*

* Tue Jan 17 2017 Dan Walsh <dwalsh@fedoraproject.org> - 2:3.1-1
- Fix labeling on /usr/bin/runc.*
- Add sandbox_net_domain access to container.te
- Remove containers ability to look at /etc content

* Wed Jan 11 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 2:2.2-4
- use upstream's RHEL-1.12 branch, commit 56c32da for CentOS 7

* Tue Jan 10 2017 Jonathan Lebon <jlebon@redhat.com> - 2:2.2-3
- properly disable docker module in %%post

* Sat Jan 07 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 2:2.2-2
- depend on selinux-policy-targeted
- relabel docker-latest* files as well

* Fri Jan 06 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 2:2.2-1
- bump to v2.2
- additional labeling for ocid

* Fri Jan 06 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 2:2.0-2
- install policy at level 200
- From: Dan Walsh <dwalsh@redhat.com>

* Fri Jan 06 2017 Lokesh Mandvekar <lsm5@fedoraproject.org> - 2:2.0-1
- Resolves: #1406517 - bump to v2.0 (first upload to Fedora as a
standalone package)
- include projectatomic/RHEL-1.12 branch commit for building on centos/rhel

* Mon Dec 19 2016 Lokesh Mandvekar <lsm5@fedoraproject.org> - 2:1.12.4-29
- new package (separated from docker)
