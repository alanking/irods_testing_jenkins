#!/usr/bin/python

# real modules
from __future__ import print_function
import argparse
import subprocess

# local
import builders
import configuration

## build_base_os_docker_image
# @return output of build_docker_image
def build_base_os_docker_image(platform_target):
    base_os = configuration.os_identifier_dict[platform_target]
    dockerfile = configuration.platform_dockerfile_map[platform_target]
    build_tag = ':'.join(['irods-build-and-test-base-os', platform_target])
    build_args = {'base_image' : base_os}
    return builders.build_docker_image(
        dockerfile=dockerfile,
        tag=build_tag,
        build_args=build_args)

def main():
    parser = argparse.ArgumentParser(description='Build base os containers')
    parser.add_argument('-p','--platform_target', type=str, required=True)
    args = parser.parse_args()

    build_output = build_os_containers(args.platform_target)
    print(build_output)

if __name__ == '__main__':
    main()
