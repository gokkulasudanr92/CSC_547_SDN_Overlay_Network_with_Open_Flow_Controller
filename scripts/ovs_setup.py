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


if __name__ == "__main__":

	# Install Open vSwtich
	install_require_packages()

	add_new_user("ovs")


	# Add two bridges 



