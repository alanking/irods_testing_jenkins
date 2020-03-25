#!/usr/bin/python

# real modules
from __future__ import print_function
import argparse
import docker
import os

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
parser.add_argument('--plugin_repo', type=str, required=True)
parser.add_argument('--plugin_commitish', type=str, required=True)
parser.add_argument('--irods_packages_build_directory', type=str, required=True)
parser.add_argument('-o', '--output_directory', type=str, required=True)
args = parser.parse_args()
print('plugin_repo:'+args.plugin_repo)
print('plugin_commitish:'+args.plugin_commitish)

# build the builder
try:
    plugin_sha = ci_utilities.get_sha_from_commitish(args.plugin_repo, args.plugin_commitish)
    plugin_name = args.plugin_repo.split('/')[-1]
    build_tag = ':'.join([args.platform_target + '-' + plugin_name +'-build', args.build_id])
    base_os_image_tag = ':'.join([args.platform_target, args.image_tag])
    print(base_os_image_tag)
    output_directory = os.path.join(args.output_directory, plugin_name)
    input_directory = args.irods_packages_build_directory
    output = builders.build_plugin_builder_image(
        base_os_image_tag=base_os_image_tag,
        image_tag=build_tag,
        plugin_repo=args.plugin_repo,
        plugin_commitish=plugin_sha,
        irods_build_directory=input_directory,
        plugin_build_directory=output_directory)
    for line in output:
        print(line)
except docker.errors.APIError:
    print('error occurred within docker daemon while building plugin builder image')
    raise

# run the builder
try:
    output_volume = {
        'host_path': output_directory,
        'bind': '/plugin_build_output'
    }
    input_volume = {
        'host_path': input_directory,
        'bind': '/irods_build'
    }
    print('using output directory:')
    print(output_volume['host_path'])
    print('using input directory:')
    print(input_volume['host_path'])
    output = runners.run_builder_image(
        image_name=build_tag,
        output_volume=output_volume,
        input_volume=input_volume)
    for line in output:
        print(line)
except docker.errors.ContainerError:
    print(build_tag + ' failed building iRODS/iCommands.')
    raise
