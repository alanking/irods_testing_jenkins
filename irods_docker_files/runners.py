#!/usr/bin/python

# real modules
from __future__ import print_function
import docker
import json
import os

# local
import configuration

## run_builder_image
# @return output of running docker container
def run_builder_image(image_name, output_directory=None):
    try:
        output_mount_dir = '/jenkins_output'
        client = docker.from_env()
        return client.containers.run(
            image_name,
            remove=True,
            volumes={
                output_directory : {
                    'bind': output_mount_dir,
                    'mode': 'rw'
                }
            }
        )
    except docker.errors.ImageNotFound:
        print(image_name + ' does not exist.')
        raise
    except docker.errors.APIError:
        print('docker daemon returned an error.')
        raise

