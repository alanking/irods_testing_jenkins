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
    dockerfile_path = os.path.join(context_dir, dockerfile)
    with open(dockerfile_path) as f:
        return [line[line.keys()[0]] for line in client.build(
            path=context_dir, fileobj=f, tag=tag, buildargs=build_args, decode=True
            )]
