#!/usr/bin/python

# real modules
from __future__ import print_function
import argparse
import docker

# local
import builders

parser = argparse.ArgumentParser(description='Build base os-containers')
parser.add_argument('-p','--platform_target', type=str, required=True)
parser.add_argument('-b','--build_id', type=str, required=True)

args = parser.parse_args()
try:
    output = builders.build_base_os_docker_image(args.platform_target, args.build_id)
    for line in output:
        print(line)
except docker.errors.APIError:
    print('builder raised docker.errors.APIError. Exiting.')
    raise
except docker.errors.DockerException:
    print('builder raised docker.errors.DockerException. Exiting.')
    raise
