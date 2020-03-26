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
from docker_cmd_builder import DockerCommandsBuilder
import docker_cmds_utilities


def run_plugin_tests(image_name, plugin_sha, machine_name, plugin_name, test_name_prefix, cmd_line_args):
    build_mount = cmd_line_args.irods_build_dir + ':/irods_build'
    results_mount = cmd_line_args.output_directory + ':/irods_test_env'
    plugin_mount = cmd_line_args.plugin_build_dir + ':/plugin_mount_dir'
    key_mount = '/projects/irods/vsphere-testing/externals/amazon_web_services-CI.keypair:/projects/irods/vsphere-testing/externals/amazon_web_services-CI.keypair'
    mysql_mount = '/projects/irods/vsphere-testing/externals/mysql-connector-odbc-5.3.7-linux-ubuntu16.04-x86-64bit.tar.gz:/projects/irods/vsphere-testing/externals/mysql-connector-odbc-5.3.7-linux-ubuntu16.04-x86-64bit.tar.gz'
    run_mount = '/tmp/$(mktemp -d):/run'
    externals_mount = cmd_line_args.externals_dir + ':/irods_externals'

    if 'centos' in machine_name:
        centosCmdBuilder = DockerCommandsBuilder()
        centosCmdBuilder.plugin_constructor(machine_name, build_mount, plugin_mount, results_mount, key_mount, None, None, externals_mount, image_name, 'install_and_test.py', cmd_line_args.database_type, cmd_line_args.plugin_repo, plugin_sha, cmd_line_args.passthrough_arguments)
        
        run_cmd = centosCmdBuilder.build_run_cmd()
        exec_cmd = centosCmdBuilder.build_exec_cmd()
        stop_cmd = centosCmdBuilder.build_stop_cmd()
    elif 'ubuntu' in machine_name:
        ubuntuCmdBuilder = DockerCommandsBuilder()
        ubuntuCmdBuilder.plugin_constructor(machine_name, build_mount, plugin_mount, results_mount, key_mount, mysql_mount, None, externals_mount, image_name, 'install_and_test.py', cmd_line_args.database_type, cmd_line_args.plugin_repo, plugin_sha, cmd_line_args.passthrough_arguments)
        
        run_cmd = ubuntuCmdBuilder.build_run_cmd()
        exec_cmd = ubuntuCmdBuilder.build_exec_cmd()
        stop_cmd = ubuntuCmdBuilder.build_stop_cmd()
    else:
        print('OS not supported')

    database_container = test_name_prefix + '_' + plugin_name + '_' + cmd_line_args.database_type + '-database'
    network_name = test_name_prefix + '_' + cmd_line_args.database_type + '_' + plugin_name
    alias_name = 'icat.example.org'

    docker_cmds_utilities.create_network(network_name)
    docker_cmds_utilities.run_database(cmd_line_args.database_type, database_container, alias_name, network_name)

    _rc = docker_cmds_utilities.run_command_in_container(run_cmd, exec_cmd, stop_cmd, machine_name, alias_name, database_container, cmd_line_args.database_type, network_name)
    sys.exit(_rc)

def main():
    parser = argparse.ArgumentParser(description='Run tests in os-containers')
    parser.add_argument('-p', '--platform_target', type=str, required=True)
    parser.add_argument('--image_tag', type=str, required=True, help='Tag id or name for the base image')
    parser.add_argument('-b', '--build_id', type=str, required=True)
    parser.add_argument('--test_name_prefix', type=str, required=True)
    parser.add_argument('--irods_build_dir', type=str, required=True)
    parser.add_argument('--externals_dir', type=str, help='externals build directory')
    parser.add_argument('--plugin_build_dir', type=str, help='plugin build directory')
    parser.add_argument('--plugin_repo', help='plugin git repo')
    parser.add_argument('--plugin_commitish', help='plugin git commit sha')
    parser.add_argument('--database_type', default='postgres', help='database type', required=True)
    parser.add_argument('-o', '--output_directory', type=str, required=True)
    parser.add_argument('--passthrough_arguments', type=str)
    
    args = parser.parse_args()
    build_tag = None
    base_image = ci_utilities.get_base_image(args.platform_target, args.image_tag)

    build_tag = ci_utilities.get_build_tag(args.platform_target, 'plugin-install', args.database_type, args.build_id)
    
    docker_cmds_utilities.build_irods_zone(build_tag, base_image, args.database_type, 'Dockerfile.install_and_test', True)
    test_name_prefix = args.platform_target + '_' + args.test_name_prefix.replace('-', '_')

    plugin_repo = args.plugin_repo
    plugin_repo_split = plugin_repo.split('/')
    plugin = plugin_repo_split[len(plugin_repo_split) - 1]
    plugin_name = plugin.split('.git')[0]
    if 'audit' in plugin_name:
        if '--message_broker' in args.passthrough_arguments:
            message_broker = args.passthrough_arguments.split(' ')[1]
            machine_name = args.platform_target + '-' + plugin_name + '-' + message_broker + '-' + args.database_type + '-' + args.build_id
    elif 'storage' in plugin_name and args.passthrough_arguments is not None and 'unified' in args.passthrough_arguments:
            plugin_name = plugin_name + '-unified'
            machine_name = args.platform_target + '-' + plugin_name + '-' + args.database_type + '-' + args.build_id
    else:
        machine_name = args.platform_target + '-' + plugin_name + '-' + args.database_type + '-' + args.build_id

    plugin_sha = ci_utilities.get_sha_from_commitish(args.plugin_repo, args.plugin_commitish)
    run_plugin_tests(build_tag, plugin_sha, machine_name, plugin_name, test_name_prefix, args)

if __name__ == '__main__':
    main()
