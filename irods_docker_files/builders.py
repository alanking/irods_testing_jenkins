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
def build_docker_image(dockerfile, tag, context_dir=os.getcwd(), build_args=None):
    client = docker.APIClient(base_url=configuration.docker_client_base_url)
    dockerfile_path = os.path.join(context_dir, dockerfile)
    with open(dockerfile_path) as f:
        return [line[line.keys()[0]] for line in client.build(
            path=context_dir, fileobj=f, tag=tag, buildargs=build_args, decode=True
            )]

## build_base_os_docker_image
# @return output of build_docker_image
def build_base_os_docker_image(platform_target, build_id='0'):
    base_os = configuration.os_identifier_dict[platform_target]
    dockerfile = configuration.platform_dockerfile_map[platform_target]
    build_tag = ':'.join([platform_target, build_id])
    build_args = {'base_image': base_os}
    return build_docker_image(dockerfile=dockerfile, tag=build_tag, build_args=build_args)

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
        'arg_irods_commitish': irods_commitish
    }
    return build_docker_image(dockerfile=dockerfile, tag=image_tag, build_args=build_args)
