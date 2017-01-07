
from jinja2 import Template
from .templates import rkt
from .templates import docker
from .version import __version__
import yaml
import argparse
import os
import sys
import re

parser = argparse.ArgumentParser(description='Convert Docker Compose files to CoreOS Fleet units')
group = parser.add_mutually_exclusive_group()
group.add_argument('-d', '--docker', action="store_true", help='select docker as the container runtime')
group.add_argument('-r', '--rkt', action="store_true", help='select rkt as the container runtime')
parser.add_argument('-o', '--output', action="store", help='select the output directory')
parser.add_argument('-v', action='version', version=__version__)
parser.add_argument('file', help='docker compose file')
args = parser.parse_args()

def get_yaml():
	"""Get the Docker Compose yaml file"""
	try:
		if re.match('.*\.ya?ml$',args.file):
			with open(args.file, 'r') as yml_file:
				compose_file = yaml.load(yml_file)
		return compose_file
	except:
		print("ERROR: File not found or not valid. Are you loading a .yaml file?")
		sys.exit(-1)

def check_output(directory):
	"""Check the output directory"""
	if args.output:
		try:
			os.stat(directory)
		except:
			os.mkdir(directory)
		path = os.path.abspath(args.output)
	else:
		path = os.getcwd()

	return path

def create_file(data, name, template, path, msg, ext):
	"""Create the unit/config file in the filesystem"""
	conf_file = name + ext
	file_data = Template(template).render(data)

	path += "/" + conf_file
	file = open(path,"wt")
	file.write(file_data)
	file.close()

	print(msg + conf_file)

def create_rkt_ports(ports):
	"""Convert the Docker compose ports format to rkt's"""
	rkt_port = []
	protocol = "tcp"

	for port in ports:
		if ":" in port:
			host_port, container_port = port.split(":")
		else:
			host_port = port
			container_port = port
		if "udp" in container_port:
			container_port, protocol = container_port.split("/")

		rkt_port.append(host_port + "-" + protocol + ":" + container_port)

	return rkt_port

def create_rkt_volumes(volumes):
	"""
	Convert the Docker compose volumes format to rkt's

	Volume types:
		- /var/lib/mysql >> NOT SUPPORTED
		- /opt/data:/var/lib/mysql >> SUPPORTED
		- datavolume:/var/lib/mysql >> SUPPORTED
		- /opt/logs:/var/log/mysql:ro >> SUPPORTED

	Return:
		- dict composed of list of dicts

	Example:
		- {'rkt_volumes':
		  	[
		  		{'rkt_host_volume': 'datavolume', 'rkt_volume': 'datavolume:/var/lib/mysql', 'rkt_volume_type': 'empty', 'read_only': 'false', 'rkt_mount_point': '/var/lib/mysql'},
		  		{'rkt_host_volume': '/opt/logs', 'rkt_volume': '/opt/logs:/var/log/mysql:ro', 'rkt_volume_type': 'host', 'rkt_mount_point': '/var/log/mysql', 'read_only': 'true', 'rkt_volume_name': 'volume-opt-logs'}
		  	]
		  }
	"""
	rkt_volumes = {}
	rkt_volume = {}
	rkt_volume_data = []

	for volume in volumes:
		if ":" in volume:
			rkt_volume['rkt_volume'] = volume
			rkt_volume['rkt_volume_type'] = "empty"
			volume_parts = volume.split(":")

			if len(volume_parts) == 3:
				host_volume, mount_point, read_only = volume_parts
				if "ro" in read_only:
					read_only = "true"
			else:
				host_volume, mount_point = volume_parts
				read_only = "false"

			rkt_volume['rkt_host_volume'] = host_volume
			if "/" in host_volume:
				rkt_volume['rkt_volume_type'] = "host"
				rkt_volume['rkt_volume_name'] = "volume" + re.sub('/','-',host_volume)
		else:
			continue

		rkt_volume['rkt_mount_point'] = mount_point
		rkt_volume['read_only'] = read_only
		rkt_volume_data.append(rkt_volume.copy())

	rkt_volumes['rkt_volumes'] = rkt_volume_data

	return rkt_volumes

def create_rkt_networks(network, subnet, path):
	"""Convert the Docker compose networks format to rkt's"""
	rkt_networks = {}
	template = rkt.rkt_net_template()

	rkt_networks['rkt_network'] = network
	rkt_networks['rkt_subnet'] = subnet

	create_file(rkt_networks, network, template, path, msg= "Created rkt network: ", ext=".conf")

def get_compose_data(compose_file, service):
	"""Get all the data of the Docker Compose file for each service"""
	compose_data = {}

	for key, value in compose_file['services'][service].items():
		compose_data[key] = value
	# Set container_name in case doesn't exist in the Docker Compose file
	if not 'container_name' in compose_data:
		compose_data['container_name'] = service

	return compose_data

def convert_to_rkt(compose_file, path):
	"""Convert the Docker compose file to Fleet unit file using Rkt"""
	#print (compose_file)
	if 'networks' in compose_file:
		i = 42
		compose_networks = [network for network in compose_file['networks']]
		for network in compose_networks:
			subnet = "10." + str(i) + ".0.0/16"
			i += 1

			create_rkt_networks(network, subnet, path)

	for service in compose_file['services']:
		compose_data = get_compose_data(compose_file, service)
		#print (compose_data)
		if 'ports' in compose_data:
			compose_data['ports'] = create_rkt_ports(compose_data['ports'])
		if 'volumes' in compose_data:
			compose_data.update(create_rkt_volumes(compose_data['volumes']))
		template = rkt.rkt_template()

		create_file(compose_data, service, template, path, msg="Rkt service created: ", ext=".service")

def convert_to_docker(compose_file, path):
	"""Convert the Docker compose file to Fleet unit file using Docker"""
	for service in compose_file['services']:
		compose_data = get_compose_data(compose_file, service)
		template = docker.docker_template()

		create_file(compose_data, service, template, path, msg="Docker service created: ", ext=".service")

def main():
	"""Convert the Docker Compose file"""
	compose_file = get_yaml()
	path = check_output(args.output)

	if args.rkt:
		convert_to_rkt(compose_file, path)
	else:
		convert_to_docker(compose_file, path)
