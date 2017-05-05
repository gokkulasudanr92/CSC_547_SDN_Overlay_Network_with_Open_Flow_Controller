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

	# VCL sandbox argument definitions
	sb_parser.add_argument("-d", "--default", help="Installs OvS and \
						replaces private and nat networks with new OvS bridges.",
                    action="store_true")
	sb_parser.add_argument("-i", "--install", help="Fetches required \
									packages for OvS and installs it.", action="store_true")

	sb_parser.add_argument("-t", "--type", help="Define sandbox type: master or slave, default: \'master\'", required=True)
	sb_parser.add_argument("-pb", "--private-bridge", help="Define the bridge interface name, default: \'ovsbr0\'")
	sb_parser.add_argument("-nb", "--nat-bridge", help="Define the bridge interface name \'ovsbr1\'")
	sb_parser.add_argument("-pip", "--private-bridge_ip", help="Define the bridge ip, default: \'192.168.100.10\'")
	sb_parser.add_argument("-nip", "--nat-bridge_ip", help="Define the bridge ip, default: \'192.168.200.10\'")

	vx_parser.add_argument("-rip", "--remote-ip", help="Remote ip for VxLan tunnel endpoint", required=True)
	vx_parser.add_argument("-b", "--bridge", help="bridge interface for tunnel", required=True)
	vx_parser.add_argument("-t", "--tun", help="tun tap interface for tunnel", required=True)
	vx_parser.add_argument("-k", "--key", help="key for the", required=True)

	# Print help if no arguments are passed
	if len(sys.argv)==1:
	    parser.print_help()
	    sb_parser.print_help()
	
	args = parser.parse_args()	        

	if(args.type != 'master' or args.type != 'slave'):
		print "Enter correct sandbox type : \'master\' or \'slave\'"
		sb_parser.print_help()

	# print args