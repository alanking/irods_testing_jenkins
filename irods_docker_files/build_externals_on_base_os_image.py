#!/usr/bin/python
from __future__ import print_function
import argparse
import docker
import os

import configuration

def build_externals_packages(
    platform_target,
    build_id,
    input_directory,
    output_directory):

    base_os_image_tag = ':'.join([configuration.base_os_image_name, platform_target])
    builder_container_name = '-'.join([platform_target, 'build_externals', build_id])
    input_directory_bind = '/externals_repo_to_build'
    output_directory_bind = '/built_packages_output'
    build_hook_path = os.path.join(input_directory_bind, configuration.build_hook_filename)
    volumes = {
        input_directory: {
            'bind': input_directory_bind,
            'mode': 'rw'
        },
        output_directory: {
            'bind': output_directory_bind,
            'mode': 'rw'
        }
    }

    # run build hook
    client = docker.from_env()
    cmd = [
        'python', build_hook_path,
        '--output_root_directory', output_directory_bind
    ]
    print('building externals from repo [{0}] on host machine (mounted in container as:[{1}])'.format(input_directory, input_directory_bind))
    print('placing packages in [{0}] on host machine (mounted in container at: [{1}])'.format(output_directory, output_directory_bind))
    return client.containers.run(
        image=base_os_image_tag,
        command=cmd,
        name=builder_container_name,
        remove=True,
        volumes=volumes)

def main():
    parser = argparse.ArgumentParser(description='Build irods in base os-containers')
    parser.add_argument('-p', '--platform_target', type=str, required=True)
    parser.add_argument('-b', '--build_id', type=str, required=True)
    parser.add_argument('-o', '--output_directory', type=str, required=True)
    parser.add_argument('--repo_directory_identifier', type=str, required=True)
    args = parser.parse_args()

    # full path on host machine which will be mounted inside build container
    input_directory = os.path.join(
        os.environ['JENKINS_OUTPUT'],
        args.repo_directory_identifier,
        args.build_id)
    #output_directory = os.path.join(
        #args.output_directory,
        #configuration.platform_packages_dir_map[args.platform_target])
    result_output = build_externals_packages(
        args.platform_target,
        args.build_id,
        input_directory,
        args.output_directory)
        #output_directory)
    print(result_output)
    print('build completed successfully')

   
if __name__ == '__main__':
    main()
