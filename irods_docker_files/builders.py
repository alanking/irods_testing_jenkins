#!/usr/bin/python

# real modules
from __future__ import print_function
import docker
import json
import os

# local
import configuration

## build_docker_image
# @return output of docker.APIClient.build as a list of strings
def build_docker_image(
    dockerfile,
    tag,
    context_dir=None,
    build_args=None):

    if context_dir is None:
        context_dir = os.getcwd()
    client = docker.APIClient(base_url=configuration.docker_client_base_url)
    return [line[line.keys()[0]] for line in client.build(
        path=context_dir,
        dockerfile=dockerfile,
        tag=tag,
        buildargs=build_args,
        decode=True
        )]

## build_base_os_image
# @return output of build_docker_image
def build_base_os_image(
    platform_target,
    build_id='0'):

    base_os = configuration.os_identifier_dict[platform_target]
    dockerfile = configuration.platform_dockerfile_map[platform_target]
    build_tag = ':'.join([platform_target, build_id])
    build_args = {'base_image': base_os}
    return build_docker_image(
        dockerfile=dockerfile,
        tag=build_tag,
        build_args=build_args)

## build_irods_builder_image
# @return output of build_docker_image
def build_irods_builder_image(
    base_os_image_tag,
    image_tag,
    irods_repo=configuration.default_irods_repo,
    irods_commitish=configuration.default_irods_commitish,
    icommands_repo=configuration.default_icommands_repo,
    icommands_commitish=configuration.default_icommands_commitish):

    dockerfile = 'Dockerfile.build_irods'
    build_args = {
        'base_image': base_os_image_tag,
        'arg_irods_repo': irods_repo,
        'arg_irods_commitish': irods_commitish,
        'arg_icommands_repo': icommands_repo,
        'arg_icommands_commitish': icommands_commitish
    }
    return build_docker_image(
        dockerfile=dockerfile,
        tag=image_tag,
        build_args=build_args)

## build_plugin_builder_image
# @return output of build_docker_image
def build_plugin_builder_image(
    base_os_image_tag,
    image_tag,
    plugin_repo,
    plugin_commitish,
    irods_build_directory,
    plugin_build_directory):

    dockerfile = 'Dockerfile.build_plugin'
    print('setting base_image arg to:')
    print(base_os_image_tag)
    build_args = {
        'base_image': base_os_image_tag,
        'arg_plugin_repo': plugin_repo,
        'arg_plugin_commitish': plugin_commitish,
        'arg_plugin_build_directory': plugin_build_directory
    }
    return build_docker_image(
        dockerfile=dockerfile,
        tag=image_tag,
        build_args=build_args)

def build_irods_runner_image(
    build_tag,
    base_image,
    dockerfile='Dockerfile.install_and_test'):

    build_args = {'base_image': base_image}
    return build_docker_image(
        dockerfile=dockerfile,
        tag=build_tag,
        build_args=build_args)

def build_database_image(database_type):
    database_image_tag = configuration.database_dict[database_type]
    if database_type is 'oracle':
        return build_docker_image(
            dockerfile='Dockerfile.xe',
            tag=database_image_tag)
    else:
        client = docker.from_env()
        database_images_list = client.images.list(name=database_image_tag)
        if not database_images_list:
            return client.images.pull(database_image_tag)
        return database_images_list

