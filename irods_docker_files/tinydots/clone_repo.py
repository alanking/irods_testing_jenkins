#!/usr/bin/python
from __future__ import print_function
import argparse
import git
import os
import shutil
import sys
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

parser = argparse.ArgumentParser(description='Clone Git Repository')
parser.add_argument('--unique_id', type=str, required=True)
parser.add_argument('--repo', type=str, required=True)
parser.add_argument('--commitish', type=str, required=True)
parser.add_argument('--clone_target_directory', type=str)
parser.add_argument('--ignore_cache', action='store_true', default=False)
args = parser.parse_args()

target_directory = args.clone_target_directory
if not target_directory:
    target_directory = os.path.join(
        '/jenkins_output',
        os.path.basename(urlparse(args.repo).path),
        args.unique_id)

if os.path.exists(target_directory):
    if not args.ignore_cache:
        print('non-empty directory found at [{0}] - skipping clone'.format(target_directory))
        sys.exit(0)
    shutil.rmtree(target_directory)

print('cloning repository from [{0}]@[{1}] to [{2}]'.format(args.repo, args.commitish, target_directory))
repo = git.Repo.clone_from(
    args.repo,
    target_directory,
    branch=args.commitish)
repo.submodule_update()
print('cloning completed successfully')
