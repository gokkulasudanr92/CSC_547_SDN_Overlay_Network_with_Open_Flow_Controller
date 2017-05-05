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

if __name__ == "__main__":

	# try:
	# Argument parsing
	parser = argparse.ArgumentParser()
	# Version info
	parser.add_argument("-v", "--version", help="version information of the script",
                    action="store_true")

	subparsers = parser.add_subparsers(help='<think of help text>')


	sb_parser = subparsers.add_parser("sbvcl", help='VCL Sandbox')
	# options to add network = nat/private
	# for each of the above add 
	# path to the network xml
	# bridge ovsbr0 or ovsbr1 
	# bridge ip address 
	# mtu optional - default 1400
	vx_parser = subparsers.add_parser("vxlan", help='Setup VxLan')

	# argument definitions
	sb_parser.add_argument("-d", "--default", help="Installs OvS and \
						replaces private and nat networks with new OvS bridges.",
                    action="store_true")
	sb_parser.add_argument("-i", "--install", help="Fetches required \
									packages for OvS and installs it.", action="store_true")

	args = parser.parse_args()	        

