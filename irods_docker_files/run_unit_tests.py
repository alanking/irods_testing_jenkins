#!/usr/bin/python

# real modules
from __future__ import print_function
import argparse
import json
import requests
import subprocess
import sys

from multiprocessing import Pool
from urlparse import urlparse

# local
import builders
import configuration
import ci_utilities
import docker_cmds_utilities
import setup_database

from docker_cmd_builder import DockerCommandsBuilder

def download_list_of_tests(irods_repo, irods_sha, relative_path):
    url = urlparse(irods_repo)

    tests_list_url = 'https://raw.github.com' + url.path + '/' + irods_sha + '/' + relative_path
    response = requests.get(tests_list_url)

    print('test list url => {0}'.format(tests_list_url))
    print('response      => {0}'.format(str(response)))
    print('response text => {0}'.format(response.text))

    return json.loads(response.text)

def run_test_in_container(
    test_runner_image_tag,
    test_runner_container_name,
    test_docker_network_name,
    database_container_name,
    database_type,
    test_name,
    alias_name=None,
    volumes=None):

    client = docker.from_env()

    # run irods container
    try:
        output = client.containers.run(
            image=test_runner_image_tag,
            command=None,
            hostname=alias_name,
            name=test_runner_container_name,
            remove=True,
            volumes=volumes
        )
        print(output)
    except docker.errors.ContainerError:
        print(test_runner_container_name + ' exited with non-zero code.')
        raise
    except docker.errors.ImageNotFound:
        print(test_runner_image_tag + ' does not exist.')
        raise

    # run database container
    if client.containers.get(test_runner_container_name).status is 'running':
        connect_to_network(test_runner_container_name, alias_name, test_docker_network_name)

    if is_container_running(database_container_name):
        # TODO: this was a "health check" before using docker inspect for oracle...
        setup_database.configure_database(
            database_type,
            database_container_name,
            test_runner_container_name,
            test_docker_network_name)

    # execute test in container
    cmd = [
        'python', 'install_and_test.py',
        '--database_type', database_type, 
        '--test_name', test_name,
        '--database_machine', database_container_name
    ]
    exec_rc, exec_output = client.containers.get(test_runner_container_name).run_exec(cmd=cmd)
    print(exec_output)

    # stop test runner and database containers, delete network
    client.containers.get(test_runner_container_name).stop()
    client.containers.get(database_container_name).stop()
    delete_network(test_docker_network_name)

    return exec_rc

def launch_parallel_tests_in_containers(
    run_pool,
    test_list,
    test_runner_image_tag,
    jenkins_output_dir,
    irods_build_dir,
    test_name_prefix,
    externals_build_dir=None,
    database_type=None
    ):

    alias_name = 'icat.example.org'
    volumes = {
        jenkins_output: {
            'bind': '/irods_test_env',
            'mode': 'rw'
        },
        irods_build_dir: {
            'bind': '/irods_build',
            'mode': 'ro'
        },
        '/sys/fs/cgroup': {
            'bind': '/sys/fs/cgroup',
            'mode': 'ro'
        }
    }
    if externals_build_dir:
        volumes[externals_build_dir] = {
            'bind': '/irods_externals',
            'mode': 'ro'
        }

    containers = list()
    for test in test_list:
        test_runner_container_name = '_'.join([test_name_prefix, test, database_type])
        test_database_container_name = '-'.join([test_runner_container_name, 'database'])
        test_docker_network_name = '_'.join([test_name_prefix, database_type, test])
        containers.extend({
            'test_name': test,
            'proc': run_pool.apply_async(
                runners.run_test_in_container,
                (
                    test_runner_image_tag=test_runner_image_tag,
                    test_runner_container_name=test_runner_container_name,
                    test_docker_network_name=test_docker_network_name,
                    database_container_name=test_database_container_name,
                    database_type=database_type,
                    test,
                    alias_name=alias_name,
                    volumes=volumes
                )
            )
        )
    return containers

def run_tests_in_parallel(
    test_runner_image_name,
    jenkins_output_dir,
    irods_build_dir,
    externals_build_dir=None,
    irods_repo=configuration.default_irods_repo,
    irods_commitish=configuration.default_irods_commitish,
    test_name_prefix,
    test_parallelism=4,
    database_type=None):

    irods_sha = ci_utilities.get_sha_from_commitish(irods_repo, irods_commitish)
    test_list = download_list_of_tests(irods_repo, irods_sha, 'unit_tests/unit_tests_list.json')

    run_pool = Pool(processes=test_parallelism)
    containers_running_tests = launch_parallel_tests_in_containers(
        run_pool,
        test_list,
        test_runner_image_tag=test_runner_image_name,
        jenkins_output_dir,
        irods_build_dir,
        externals_build_dir,
        test_name_prefix,
        database_type)

    container_error_codes = [
        {
            'test_name': c['test_name'],
            'error_code': c['proc'].get()
        }
        for c in containers_running_tests
    ]

    print(container_error_codes)

    failures = []
    for ec in container_error_codes:
        if ec['error_code'] != 0:
            failures.append(ec['test_name'])

    if len(failures) > 0:
        print('Failing Tests:')
        for test_name in failures:
            print('\t{0}'.format(test_name))
        sys.exit(1)


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

    # build test runner image and database iamge
    base_image = ci_utilities.get_base_image(args.platform_target, args.image_tag)
    build_tag = ci_utilities.get_build_tag(args.platform_target, 'irods-install', args.database_type, args.build_id)
    builders.build_irods_runner_image(build_tag, base_image, 'Dockerfile.install_and_test')
    builders.build_database_image(args.database_type)

    # run tests
    test_name_prefix = '_'.join(args.platform_target, args.test_name_prefix.replace('-', '_'))
    irods_sha = ci_utilities.get_sha_from_commitish(args.irods_repo, args.irods_commitish)
    run_tests(build_tag, irods_sha, test_name_prefix, args)

    run_tests_in_parallel(
        test_runner_image_name=build_tag,
        jenkins_output_dir=args.output_directory,
        irods_build_dir=args.irods_build_dir,
        externals_build_dir=args.externals_dir,
        irods_repo=args.irods_repo,
        irods_commitish=args.irods_sha,
        test_name_prefix=test_name_prefix,
        test_parallelism=args.test_parallelism,
        database_type=args.database_type)

if __name__ == '__main__':
    main()
