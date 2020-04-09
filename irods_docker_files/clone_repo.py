#!/usr/bin/python
from __future__ import print_function
import argparse
import git
import os
import shutil
import sys

parser = argparse.ArgumentParser(description='Clone Git Repository')
parser.add_argument('-b', '--build_id', type=str, required=True)
parser.add_argument('--repo', type=str, required=True)
parser.add_argument('--commitish', type=str, required=True)
parser.add_argument('--repo_directory_identifier', type=str, required=True)
parser.add_argument('--ignore_cache', action='store_true', default=False)
args = parser.parse_args()

# TODO: Turn '/jenkins_output' into environment variable or configuration value
# Full path to destination within the "wormhole" mountpoint inside the Jenkins container
repo_directory = os.path.join('/jenkins_output', args.repo_directory_identifier, args.build_id)
if os.path.exists(repo_directory):
    if not args.ignore_cache:
        print('using previously cloned repository at ' + repo_directory)
        sys.exit(0)

    shutil.rmtree(repo_directory)

print('cloning repository from [{0}]@[{1}] to [{2}]'.format(args.repo, args.commitish, repo_directory))
repo = git.Repo.clone_from(
    args.repo,
    repo_directory,
    branch=args.commitish)
repo.submodule_update()
print('cloning completed successfully')
