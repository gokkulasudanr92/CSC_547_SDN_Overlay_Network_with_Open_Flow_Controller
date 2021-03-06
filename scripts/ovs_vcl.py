#! /usr/bin/python
# Run the script as root
from subprocess import Popen, PIPE, STDOUT
import subprocess
import os
import argparse
import sys
remote_public = "152.46.17.251"
remote_private = "10.25.5.41"
is_master = True

if is_master is True:
	ovs_private_ip = "192.168.100.10"
	ovs_public_ip = "192.168.200.10"
else:
	ovs_private_ip = "192.168.100.11"
	ovs_public_ip = "192.168.200.11"

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

# Source: http://costiser.ro/2016/07/07/overlay-tunneling-with-openvswitch-gre-vxlan-geneve-greoipsec/#.WPWEgVMrLwe
def create_tunnel(remote_ip, tun_tap, bridge, key):
	cmd_create_tunnel = ['ovs-vsctl', 'add-port', bridge, tun_tap, \
						'--', 'set', 'interface', tun_tap, 'type=vxlan' , \
						('options:remote_ip=%s' % remote_ip), ('options:key=%s' % key)]
	subprocess.call(cmd_create_tunnel)

def update_firewall_for_tunnel(remote_ip, port,protocol):
	cmd_add_firewall_rule_vxlan = ['iptables', '-I', 'INPUT', '-s', \
								('%s/32' % remote_ip), '-p', protocol, \
								'-m', protocol, '--dport', port, '-j', 'ACCEPT']
	subprocess.call(cmd_add_firewall_rule_vxlan)
	
def update_firewall_for_port_redirection(src_ip, dest_ip,in_port, redirect_to_port,protocol):
        cmd_add_firewall_rule_vxlan = ['iptables', '-t', 'nat', '-I', 'PREROUTING', '-s', ('%s/32' % src_ip),  \
                                                                '-d', ('%s/32' % dest_ip),\
                                                                '-p', protocol, \
                                                                '-m', protocol, '--dport', in_port, '-j', 'REDIRECT',  '--to-ports', redirect_to_port]
        subprocess.call(cmd_add_firewall_rule_vxlan)


def change_mtu_size(bridge, mtu_size):
	cmd_change_mtu_size = ['ifconfig', bridge, 'mtu', mtu_size]
	subprocess.call(cmd_change_mtu_size)

def change_ssh_hostonly_config(bridge_ip):
	cmd_change_ssh_hostonly_config = ['sed', '-i', ("'s/ListenAddress 192.168.100.10/ListenAddress %s/g'" % bridge_ip),\
										'/etc/ssh/hostonly_sshd_config']
	cmd_load_ssh_hostonly_config = ['systemctl', 'restart', 'hostonly_sshd.service']

	cmd_list = [cmd_change_ssh_hostonly_config, cmd_load_ssh_hostonly_config]

	for cmd in cmd_list:
		subprocess.call(cmd)

def argument_parsing():
	# Argument parsing
	parser = argparse.ArgumentParser()
	# Version info
	parser.add_argument("-v", "--version", help="version information of the script",
                    action="store_true")

	subparsers = parser.add_subparsers(help='<think of help text>')


	sb_parser = subparsers.add_parser("sbvcl", help='VCL Sandbox', action="store_true")
	
	vx_parser = subparsers.add_parser("vxlan", help='Setup VxLan', action="store_true")

	# VCL sandbox argument definitions
	sb_parser.add_argument("-d", "--default", help="Installs OvS and \
						replaces private and nat networks with new OvS bridges.",
                    action="store_true")
	sb_parser.add_argument("-i", "--install", help="Fetches required \
									packages for OvS and installs it.", action="store_true")
	sb_parser.add_argument("-ni", "--no-install", help="Does not install ovs packages", action="store_true")

	sb_parser.add_argument("-t", "--type", help="Define sandbox type: master or slave. default type: \'master\' \
			default behavior: Installs OvS and replaces private and nat networks with new OvS bridges.", required=True)
	sb_parser.add_argument("-pb", "--private-bridge", help="Define private bridge interface name, default: \'ovsbr0\'")
	sb_parser.add_argument("-nb", "--nat-bridge", help="Define nat bridge interface name, default: \'ovsbr1\'")
	sb_parser.add_argument("-pip", "--private-bridge-ip", help="Define private bridge ip, default: \'192.168.100.10\'")
	sb_parser.add_argument("-nip", "--nat-bridge-ip", help="Define nat bridge ip, default: \'192.168.200.10\'")

	vx_parser.add_argument("-rip", "--remote-ip", help="Remote ip for VxLan tunnel endpoint", required=True)
	vx_parser.add_argument("-b", "--bridge", help="bridge interface for tunnel", required=True)
	vx_parser.add_argument("-t", "--tun", help="tun tap interface for tunnel", required=True)
	vx_parser.add_argument("-k", "--key", help="key for the vxlan tunnel")

	# Print help if no arguments are passed
	if len(sys.argv)==1:
	    parser.print_help()
	    sb_parser.print_help()
	    vx_parser.print_help()
	
	args = parser.parse_args()	        

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



if __name__ == "__main__":

	args = argument_parsing()
	print args

	if(args.install):
		install_ovs_required_packages()
		add_new_user("ovs")
		install_ovs_packages()

	if(args.type == 'master' and args.default):

		setup_ovs_network(args.type, "private", "/etc/libvirt/qemu/networks/private.xml", \
							"ovsbr0", ovs_private_ip)

		setup_ovs_network(args.type, "nat", "/etc/libvirt/qemu/networks/nat.xml", \
						"ovsbr1", ovs_public_ip)

		change_firewall_rules("/etc/sysconfig/iptables")

		

		#def create_tunnel(remote_ip, tun_tap, bridge, key):
		create_tunnel(remote_private, "tun0", "ovsbr0", "123")
		create_tunnel(remote_public, "tun1", "ovsbr1", "456")

		#def update_firewall_for_port_redirection(src_ip, dest_ip,in_port, redirect_to_port,protocol):
		if is_master is False:
	        	update_firewall_for_port_redirection("192.168.100.1", ovs_private_ip, "22", "24", "tcp")
		
		#def update_firewall_for_tunnel(remote_ip, port,protocol):
		update_firewall_for_tunnel(remote_private, "4789", "udp")	
		update_firewall_for_tunnel(remote_private, "4789", "tcp")	
		update_firewall_for_tunnel(remote_public, "4789", "udp")	
		update_firewall_for_tunnel(remote_public, "4789", "tcp")	

		#def change_mtu_size(bridge, mtu_size):
		change_mtu_size("ovsbr0", "1400")
		change_mtu_size("ovsbr1", "1400")
		
		#def change_ssh_hostonly_config(bridge_ip):
