#! /usr/bin/python
# Run the script as root
from subprocess import Popen, PIPE, STDOUT
import subprocess
import os
import argparse
import sys

def install_ovs_required_packages():
	
	req_packages = ['gcc', 'make', 'python-devel', \
					'openssl-devel', 'kernel-devel', 'graphviz', 
					'kernel-debug-devel', 'autoconf', 'automake', \
					'rpm-build', 'redhat-rpm-config', 'libtool']
	install_package = ['yum', '-y', 'install', 'wget'] + req_packages
	subprocess.call(install_package)

def add_new_user(user_name):
	add_user = ['adduser', user_name]
	subprocess.call(add_user)

# Installation instrcutions source:
# https://n40lab.wordpress.com/2015/06/28/centos-7-installing-openvswitch-2-3-2-lts/
def install_ovs_packages():
	run_as_ovs = ['runuser', '-l', 'ovs', '-c']
	
	cmd_mk_ovs_dir = ['mkdir -p ~/rpmbuild/SOURCES']
	cmd_fetch_ovs = ['wget http://openvswitch.org/releases/openvswitch-2.5.2.tar.gz']
	cmd_cp_ovs_tar = ['cp openvswitch-2.5.2.tar.gz ~/rpmbuild/SOURCES/']
	cmd_untar_ovs = ['tar xfz openvswitch-2.5.2.tar.gz']
	cmd_rpmbuild = ['rpmbuild -bb --nocheck openvswitch-2.5.2/rhel/openvswitch.spec']
	
	cmd_list = [cmd_mk_ovs_dir, cmd_fetch_ovs, cmd_cp_ovs_tar, cmd_untar_ovs, cmd_rpmbuild]

	for cmd in cmd_list:
		subprocess.call(run_as_ovs + cmd)

	# create ovs config directory
	cmd_config_dir = ['mkdir', '/etc/openvswitch']
	cmd_install_rpm = ['yum', 'localinstall', '/home/ovs/rpmbuild/RPMS/x86_64/openvswitch-2.5.2-1.x86_64.rpm']
	cmd_start_ovs_service = ['systemctl', 'start', 'openvswitch.service']
	cmd_enable_ovs_onboot = ['chkconfig', 'openvswitch', 'on']

	# create ovs config directory
	subprocess.call(cmd_config_dir)

	# Install openvswitch rpm
	p = Popen(cmd_install_rpm, stdin=PIPE, stderr=PIPE)
	stdout_data = p.communicate(input='y')[0]
	
	cmd_list = [cmd_start_ovs_service, cmd_enable_ovs_onboot]

	for cmd in cmd_list:
	 	subprocess.call(cmd)

# Backup config can be found under /tmp/
def create_backup(network):
	cmd_backup = ['virsh', 'net-dumpxml', network, '>', \
				'/tmp/original_' + network + '_config.xml']

	subprocess.call(create_backup)

def ovs_xml_config(file_path, network, bridge):
	file = open(file_path, 'w+')
	file.write("<network>\n")
	file.write("<name>%s</name>\n" % network)
	file.write("<forward mode='bridge'/>\n")
	file.write("<bridge name='%s'/>\n" % bridge)
	file.write("<virtualport type='openvswitch'/>\n")
	file.write("</network>")
	file.close()

def destroy_old_network(network):
	cmd_destroy = ['virsh', 'net-destroy', network]
	cmd_undefine = ['virsh', 'net-undefine', network]
	subprocess.call(cmd_destroy)
	subprocess.call(cmd_undefine)

def start_new_network(network, network_config_path):
	cmd_define = ['virsh', 'net-define', network_config_path]
	cmd_autostart = ['virsh', 'net-autostart', network]
	cmd_start = ['virsh', 'net-start', network]
	
	cmd_list = [cmd_define, cmd_autostart, cmd_start]
	
	for cmd in cmd_list:
		subprocess.call(cmd)

def assign_bridge_ip(bridge, bridge_ip):
	cmd_bridge_ip = ['ifconfig', bridge, bridge_ip]
	subprocess.call(cmd_bridge_ip)

def add_new_bridge(bridge):
	cmd_new_bridge = ['ovs-vsctl', 'add-br', bridge]
	subprocess.call(cmd_new_bridge)

def create_ovs_network(network, network_config_path, bridge, bridge_ip):
	destroy_old_network(network)
	ovs_xml_config(network_config_path, network, bridge)
	add_new_bridge(bridge)
	assign_bridge_ip(bridge, bridge_ip)
	start_new_network(network, network_config_path)


def change_firewall_rules(config_firewall_path):
	cmd_replace_virbr_to_ovsbr = ['sed', '-i.bak', 's/virbr/ovsbr/g', config_firewall_path]
	subprocess.call(cmd_replace_virbr_to_ovsbr)

	cmd_restart_ip_tables = ['service', 'iptables', 'restart']
	subprocess.call(cmd_restart_ip_tables)

def new_dhcp_conf(network, bridge):
	# file path
	base_dir = "/var/lib/libvirt/dnsmasq/"
	base_dir_pid = "/var/lib/libvirt/network/"
	file_path = base_dir + network + ".conf"

	if(network == "nat"):
		dhcp_range = "192.168.200.128,192.168.200.254"
	else:
		dhcp_range = "192.168.100.128,192.168.100.254"

	file = open(file_path, 'w+')

	file.write("strict-order\n")
	file.write("domain=%s\n" % network)
	file.write("expand-hosts\n")
	file.write("pid-file=%s\n" % (base_dir_pid + network + ".pid"))
	file.write("except-interface=lo\n")
	file.write("bind-dynamic\n")
	file.write("interface=%s\n" % bridge)

	if(network == "private"):
		file.write("dhcp-option=3\n")

	file.write("dhcp-range=%s\n" % dhcp_range)
	file.write("dhcp-no-override\n")
	file.write("dhcp-lease-max=127\n")
	file.write("dhcp-hostsfile=%s\n" % (base_dir + network + ".hostsfile"))
	file.write("addn-hosts=%s\n" % (base_dir + network + ".addnhosts"))
	file.close()

def new_dhcp_hostsfile(network):
	base_dir = "/var/lib/libvirt/dnsmasq/"
	file_path = base_dir + network + ".hostsfile"

	file = open(file_path, 'w+')
	if(network == "nat"):
		file.write("52:54:00:3d:85:f0,192.168.200.1\n")
	else:
		file.write("52:54:00:b8:33:d4,192.168.100.1\n")
		file.write("52:54:00:ae:cf:00,192.168.100.101\n")
		file.write("52:54:00:ae:cf:02,192.168.100.102\n")
		file.write("52:54:00:ae:cf:04,192.168.100.103\n")
		file.write("52:54:00:ae:cf:06,192.168.100.104\n")
	file.close()

def new_dhcp_addnhosts(network):
	base_dir = "/var/lib/libvirt/dnsmasq/"
	file_path = base_dir + network + ".addnhosts"
	cmd_create_new_addnhosts_file = ['touch', file_path]
	subprocess.call(cmd_create_new_addnhosts_file)

def load_new_dhcp_config(network, bridge):
	base_dir = "/var/lib/libvirt/dnsmasq/"
	cmd_start_dnsmasq = ['/sbin/dnsmasq', ('--conf-file=%s' % (base_dir + network + ".conf")),
						('--log-facility=%s' % (base_dir + network + ".log"))]

	cmd_list = [cmd_start_dnsmasq]
	for cmd in cmd_list:
		subprocess.call(cmd)

def configure_dhcp(network, bridge):
	new_dhcp_conf(network, bridge)
	new_dhcp_hostsfile(network)
	new_dhcp_addnhosts(network)
	load_new_dhcp_config(network, bridge)

def change_ssh_hostonly_config(bridge_ip):
	cmd_change_ssh_hostonly_config = ['sed', '-i', ("'s/ListenAddress 192.168.100.10/ListenAddress %s/g'" % bridge_ip),\
										'/etc/ssh/hostonly_sshd_config']
	cmd_load_ssh_hostonly_config = ['systemctl', 'restart', 'hostonly_sshd.service']

	cmd_list = [cmd_change_ssh_hostonly_config, cmd_load_ssh_hostonly_config]

	for cmd in cmd_list:
		subprocess.call(cmd)

def argument_parsing():
	# Argument parsing
	sb_parser = argparse.ArgumentParser()
	# Version info
	sb_parser.add_argument("-v", "--version", help="version information of the script",
                    action="store_true")
	
	# VCL sandbox argument definitions
	sb_parser.add_argument("-d", "--default", help="Installs OvS and \
						replaces private and nat networks with new OvS bridges.",
                    action="store_true")
	sb_parser.add_argument("-i", "--install", help="Fetches required \
									packages for OvS and installs it.", action="store_true")

	sb_parser.add_argument("-t", "--type", help="Define sandbox type: master or slave. default type: \'master\' \
			default behavior: Installs OvS and replaces private and nat networks with new OvS bridges.", required=True)
	sb_parser.add_argument("-pb", "--private-bridge", help="Define private bridge interface name, default: \'ovsbr0\'")
	sb_parser.add_argument("-nb", "--nat-bridge", help="Define nat bridge interface name, default: \'ovsbr1\'")
	sb_parser.add_argument("-pip", "--private-bridge-ip", help="Define private bridge ip, default: \'192.168.100.10\'")
	sb_parser.add_argument("-nip", "--nat-bridge-ip", help="Define nat bridge ip, default: \'192.168.200.10\'")

	# Print help if no arguments are passed
	if len(sys.argv)==1:
	    sb_parser.print_help()
	
	args = sb_parser.parse_args()	        

	if(args.type != 'master' and args.type != 'slave'):
		print "Enter correct sandbox type : \'master\' or \'slave\'"
		sb_parser.print_help()

	return args

def setup_ovs_network(sb_type, network, xml_path, bridge, bridge_ip):
	create_ovs_network(network, xml_path, bridge, bridge_ip)
	if sb_type == 'master':
		print "Configuring DHCP on Master"
		configure_dhcp("private", "ovsbr0")
		configure_dhcp("nat", "ovsbr1")
	else:
		print "Slave..Not configuring DHCP"

	if(network == 'private' and bridge_ip != '192.168.100.10'):
		change_ssh_hostonly_config(bridge_ip)

if __name__ == "__main__":

	args = argument_parsing()
	print args

	NAT_BRIDGE = args.nat_bridge or 'ovsbr1'
	NAT_BRIDGE_IP = args.nat_bridge_ip or '192.168.200.10'
	PRIVATE_BRIDGE = args.private_bridge or 'ovsbr0'
	PRIVATE_BRIDGE_IP = args.private_bridge_ip or '192.168.100.10'

	SB_TYPE = args.type or 'master'

	print NAT_BRIDGE, NAT_BRIDGE_IP, PRIVATE_BRIDGE, PRIVATE_BRIDGE_IP, SB_TYPE

	if(args.install):
		install_ovs_required_packages()
		add_new_user("ovs")
		install_ovs_packages()

	if(args.version):
		print "Write version info"

	setup_ovs_network(SB_TYPE, "private", "/etc/libvirt/qemu/networks/private.xml", \
						PRIVATE_BRIDGE, PRIVATE_BRIDGE_IP)

	setup_ovs_network(SB_TYPE, "nat", "/etc/libvirt/qemu/networks/nat.xml", \
					NAT_BRIDGE_IP, NAT_BRIDGE_IP)

	change_firewall_rules("/etc/sysconfig/iptables")
	
