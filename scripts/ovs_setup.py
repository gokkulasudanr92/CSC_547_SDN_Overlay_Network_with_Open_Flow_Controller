#! /usr/bin/python

import subprocess
import os

def install_require_packages: 
	
	req_packages = ['gcc', 'make', 'python-devel', \
					'openssl-devel', 'kernel-devel', 'graphviz', 
					'kernel-debug-devel', 'autoconf', 'automake', \
					'rpm-build', 'redhat-rpm-config', 'libtool']
	install_package = ['yum', '-y', 'install', 'wget'] + req_packages
	subprocess.call(install_package)


def add_new_user(user_name):
	add_user = ['adduser', user_name]
	subprocess.call(add_user)
	# Start a ovs shell
	subprocess.call(['su', '-', user_name])

def ovs_xml_config(file, network, bridge):
	file = open(file, 'w+')
	file.write("<network>\n")
	file.write("<name>%s</name>\n" % network)
	file.write("<forward mode='bridge'/>\n")
	file.write("<bridge name='%s'/>\n" % bridge)
	file.write("<virtualport type='openvswitch'/>")
	file.write("</network>")
	file.close()

# def create_backup(network):

def destroy_old_network(network):
	cmd_destroy = ['virsh', 'net-destroy', network]
	cmd_undefine = ['virsh', 'net-undefine', network]
	subprocess.call(cmd_destroy)
	subprocess.call(cmd_undefine)

def start_new_network(network, network_config_path):
	cmd_define = ['virsh', 'net-define', network_config_path]
	cmd_autostart = ['virsh', 'net-autostart', network]
	cmd_start = ['virsh', 'net-define', network]
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
	install_require_packages()

	add_new_user("ovs")

	# Add two bridges 
	create_ovs_network("private")

	


