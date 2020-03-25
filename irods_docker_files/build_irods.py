#!/usr/bin/python

# real modules
from __future__ import print_function
import argparse
import docker

# local
import builders
import ci_utilities
import configuration
import runners

# parse the args
parser = argparse.ArgumentParser(description='Build irods in base os-containers')
parser.add_argument('-p', '--platform_target', type=str, required=True)
parser.add_argument('--image_tag', type=str, required=True, help='Tag id or name for the base image')
parser.add_argument('-b', '--build_id', type=str, required=True)
parser.add_argument('--irods_repo', type=str, required=True)
parser.add_argument('--irods_commitish', type=str, required=True)
parser.add_argument('--icommands_repo', type = str, required=True)
parser.add_argument('--icommands_commitish', type=str, required=True)
parser.add_argument('-o', '--output_directory', type=str, required=True)
args = parser.parse_args()
print('irods_repo:'+args.irods_repo)
print('irods_commitish:'+args.irods_commitish)
print('icommands_repo:'+args.icommands_repo)
print('icommands_commitish:'+args.icommands_commitish)

# build the builder
try:
    irods_sha = ci_utilities.get_sha_from_commitish(args.irods_repo, args.irods_commitish)
    icommands_sha = ci_utilities.get_sha_from_commitish(args.icommands_repo, args.icommands_commitish)
    build_tag = ':'.join([args.platform_target + '-irods-build', args.build_id])
    base_os_image_tag = ':'.join([args.platform_target, args.image_tag])
    output = builders.build_irods_builder_image(
        base_os_image_tag=base_os_image_tag,
        image_tag=build_tag,
        irods_repo=args.irods_repo,
        irods_commitish=irods_sha,
        icommands_repo=args.icommands_repo,
        icommands_commitish=icommands_sha)
    for line in output:
        print(line)
except docker.errors.APIError:
    print('error occurred within docker daemon while building iRODS builder image')
    raise

# run the builder
try:
    output_volume = {
        'host_path': args.output_directory,
        'bind': '/jenkins_output'
    }
    output = runners.run_builder_image(
        image_name=build_tag,
        output_volume=output_volume)
    for line in output:
        print(line)
except docker.errors.ContainerError:
    print(image_name + ' failed building iRODS/iCommands.')
    raise
