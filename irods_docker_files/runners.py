#!/usr/bin/python

# real modules
from __future__ import print_function
import docker
import json
import os

# local
import configuration

## run_builder_image
# Equivalent to docker run of the given image name with volume mounts for input and output.
# @param image_name - name of the docker image to run
# @param output_volume - volume mount for build output (see: https://docker-py.readthedocs.io/en/stable/containers.html)
# @param input_volume - volume mount for build input (see: https://docker-py.readthedocs.io/en/stable/containers.html)
# @return output of running docker container
def run_builder_image(
    image_name,
    output_volume,
    input_volume=None):

    volumes = {
        output_volume['host_path']: {
            'bind': output_volume['bind'],
            'mode': 'rw'
        }
    }
    if input_volume is not None:
        volumes[input_volume['host_path']] = {
            'bind': input_volume['bind'],
            'mode': 'ro'
        }

    try:
        client = docker.from_env()
        return client.containers.run(
            image=image_name,
            command=None,
            remove=True,
            volumes=volumes
        )
    except docker.errors.ImageNotFound:
        print(image_name + ' does not exist.')
        raise
    except docker.errors.APIError:
        print('docker daemon returned an error.')
        raise

