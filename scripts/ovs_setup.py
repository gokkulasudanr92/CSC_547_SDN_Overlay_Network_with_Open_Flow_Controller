#! /usr/bin/python
# Run the script as root
from subprocess import Popen, PIPE, STDOUT
import subprocess
import os

def install_required_packages():
	
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
	# run_as_ovs = ['runuser', '-l', 'ovs', '-c']
	
	# cmd_mk_ovs_dir = ['mkdir -p ~/rpmbuild/SOURCES']
	# cmd_fetch_ovs = ['wget http://openvswitch.org/releases/openvswitch-2.5.2.tar.gz']
	# cmd_cp_ovs_tar = ['cp openvswitch-2.5.2.tar.gz ~/rpmbuild/SOURCES/']
	# cmd_untar_ovs = ['tar xfz openvswitch-2.5.2.tar.gz']
	# cmd_rpmbuild = ['rpmbuild -bb --nocheck openvswitch-2.5.2/rhel/openvswitch.spec']
	
	# cmd_list = [cmd_mk_ovs_dir, cmd_fetch_ovs, cmd_cp_ovs_tar, cmd_untar_ovs, cmd_rpmbuild]

	# for cmd in cmd_list:
	# 	subprocess.call(run_as_ovs + cmd)

	# create ovs config directory
	cmd_config_dir = ['mkdir', '/etc/openvswitch']
	cmd_install_rpm = ['yum', 'localinstall', '/home/ovs/rpmbuild/RPMS/x86_64/openvswitch-2.5.2-1.x86_64.rpm']
	cmd_start_ovs_service = ['systemctl', 'start', 'openvswitch.service']
	cmd_enable_ovs_onboot = ['chkconfig', 'openvswitch', 'on']

	p = Popen(cmd_install_rpm, stdin=PIPE, stderr=PIPE)
	stdout_data = p.communicate(input='y')[0]
	cmd_list = [cmd_start_ovs_service, cmd_enable_ovs_onboot]

	for cmd in cmd_list:
	 	subprocess.call(cmd)

# def create_backup(network):

def ovs_xml_config(file, network, bridge):
	file = open(file, 'w+')
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
	subprocess.call(cmd_destroy)

def add_new_bridge(bridge):
	cmd_new_bridge = ['ovs-vsctl', 'add-br', bridge]
	subprocess.call(cmd_new_bridge)

def create_ovs_network(network):
	destroy_old_network("private")
	ovs_xml_config("/tmp/new_config.xml", network, "ovsbr0")
	add_new_bridge("ovsbr0")
	start_new_network(network, "/tmp/new_config.xml")

if __name__ == "__main__":

	# Install Open vSwtich
	# install_required_packages()

	# add_new_user("ovs")

	install_ovs_packages()

	# Add two bridges 
	# create_ovs_network("private")




