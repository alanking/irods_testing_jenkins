#!/usr/bin/python

# real modules
from __future__ import print_function
import argparse
import subprocess
from subprocess import Popen, PIPE
import sys

# local
import configuration
import ci_utilities
import docker_cmds_utilities


def run_tests(image_name, irods_sha, test_name_prefix, cmd_line_args, skip_unit_tests=False):
    # build options list for run_tests_in_parallel
    options = []
    options.append(['--image_name', image_name])
    options.append(['--jenkins_output', cmd_line_args.output_directory])
    options.append(['--test_name_prefix', test_name_prefix])
    options.append(['-b', cmd_line_args.irods_build_dir])
    options.append(['--database_type', cmd_line_args.database_type])
    options.append(['--irods_repo', cmd_line_args.irods_repo])
    options.append(['--irods_commitish', irods_sha])
    options.append(['--test_parallelism', cmd_line_args.test_parallelism])
    options.append(['--externals_dir', cmd_line_args.externals_dir])
    options.append(['--run_timing_tests'])

    run_tests_cmd_list = ['python', 'run_tests_in_parallel.py']
    for option in options:
        run_tests_cmd_list.extend(option)
    print(run_tests_cmd_list)
    run_tests_p = subprocess.check_call(run_tests_cmd_list)

def main():
    parser = argparse.ArgumentParser(description='Run tests in os-containers')
    parser.add_argument('-p', '--platform_target', type=str, required=True)
    parser.add_argument('--image_tag', type=str, required=True, help='Tag id or name for the base image')
    parser.add_argument('-b', '--build_id', type=str, required=True)
    parser.add_argument('--irods_repo', type=str, required=False)
    parser.add_argument('--irods_commitish', type=str, required=False)
    parser.add_argument('--test_name_prefix', type=str, required=True)
    parser.add_argument('--irods_build_dir', type=str, required=True)
    parser.add_argument('--externals_dir', type=str, help='externals build directory')
    parser.add_argument('--database_type', default='postgres', help='database type', required=True)
    parser.add_argument('--test_parallelism', default='4', help='The number of tests to run in parallel', required=False)
    parser.add_argument('-o', '--output_directory', type=str, required=True)
    args = parser.parse_args()

    base_image = ci_utilities.get_base_image(args.platform_target, args.image_tag)
    build_tag = ci_utilities.get_build_tag(args.platform_target, 'irods-install', args.database_type, args.build_id)
    docker_cmds_utilities.build_irods_zone(build_tag, base_image, args.database_type, 'Dockerfile.install_and_test', True)
    test_name_prefix = args.platform_target + '_' + args.test_name_prefix.replace('-', '_')

    irods_sha = ci_utilities.get_sha_from_commitish(args.irods_repo, args.irods_commitish)
    run_tests(build_tag, irods_sha, test_name_prefix, args, args.skip_unit_tests)

if __name__ == '__main__':
    main()
