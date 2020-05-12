#!/usr/bin/python
from __future__ import print_function

import argparse
import irods_python_ci_utilities
import subprocess
import os
import tempfile
import time

from subprocess import Popen, PIPE

def run_docker_command(docker_cmd):
    exec_cmd = Popen(docker_cmd, stdout=PIPE, stderr=PIPE)
    _out, _err = exec_cmd.communicate()

def install_oracle_dependencies_yum():
    tar_file = os.path.expanduser('/oci.tar')
    irods_python_ci_utilities.subprocess_get_output(['wget', 'http://people.renci.org/~jasonc/irods/oci.tar', '-O', tar_file], check_rc=True)
    tar_dir = os.path.expanduser('/oci')
    os.mkdir(tar_dir)
    irods_python_ci_utilities.subprocess_get_output(['tar', '-xf', tar_file, '-C', tar_dir], check_rc=True)
    irods_python_ci_utilities.install_os_packages(['unixODBC'])
    irods_python_ci_utilities.subprocess_get_output('rpm -i --nodeps {0}/*'.format(tar_dir), shell=True, check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['ln', '-s', '/usr/lib64/libodbcinst.so.2', '/usr/lib64/libodbcinst.so.1'], check_rc=True)

def install_oracle_dependencies_apt():
    tar_file = os.path.expanduser('/oci.tar')
    irods_python_ci_utilities.subprocess_get_output(['wget', 'http://people.renci.org/~jasonc/irods/oci.tar', '-O', tar_file], check_rc=True)
    tar_dir = os.path.expanduser('/oci')
    os.mkdir(tar_dir)
    irods_python_ci_utilities.subprocess_get_output(['tar', '-xf', tar_file, '-C', tar_dir], check_rc=True)
    Popen(['apt-get', 'update']).wait()
    irods_python_ci_utilities.install_os_packages(['alien', 'libaio1'])
    irods_python_ci_utilities.subprocess_get_output('alien -i {0}/*'.format(tar_dir), shell=True, check_rc=True)

def install_oracle_client():
    with tempfile.NamedTemporaryFile() as f:
        f.write('''
export LD_LIBRARY_PATH=/usr/lib/oracle/11.2/client64/lib:$LD_LIBRARY_PATH
export ORACLE_HOME=/usr/lib/oracle/11.2/client64
export PATH=$ORACLE_HOME/bin:$PATH
''')
        f.flush()
        irods_python_ci_utilities.subprocess_get_output(['su', '-c', "cat '{0}' >> /etc/profile.d/oracle.sh".format(f.name)], check_rc=True)
        irods_python_ci_utilities.subprocess_get_output(['su', '-c', "echo 'ORACLE_HOME=/usr/lib/oracle/11.2/client64' >> /etc/environment"], check_rc=True)
        subprocess.check_call('mkdir -p /usr/lib/oracle/11.2/client64/network/admin', shell=True)
        tns_contents = '''
XE =
  (DESCRIPTION =
    (ADDRESS = (PROTOCOL = TCP)(HOST = oracle.example.org)(PORT = 1521))
    (CONNECT_DATA =
      (SERVER = DEDICATED)
      (SERVICE_NAME = XE)
    )
  )
'''
        irods_python_ci_utilities.subprocess_get_output(['sudo', 'su', '-c', "echo '{0}' > /usr/lib/oracle/11.2/client64/network/admin/tnsnames.ora".format(tns_contents)], check_rc=True)

def extract_mysql_odbc_connector():
    version = {'major':'5', 'minor':'3', 'patch':'13'}
    odbc_name = 'mysql-connector-odbc-{0}-linux-ubuntu{1}.04-x86-64bit'.format(
        '.'.join([v for v in version.values()]),
        irods_python_ci_utilities.get_distribution_version_major())
    path_to_archive = '/{}.tar.gz'.format(odbc_name)
    url_to_archive = 'https://downloads.mysql.com/archives/get/p/10/file/{}.tar.gz'.format(odbc_name)
    tar_output_dir = tempfile.mkdtemp(prefix='irods_mysql_connector_tar_extraction')

    # get the tar.gz, extract it into a directory, and copy needed contents into /usr/lib
    irods_python_ci_utilities.subprocess_get_output(['wget', '-O', path_to_archive, url_to_archive, '--directory', tar_output_dir], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['tar', 'xf', path_to_archive, '--directory', tar_output_dir], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', 'cp', os.path.join(tar_output_dir, odbc_name, 'lib', 'libmyodbc{}a.so'.format(version['major'])), '/usr/lib'], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', 'cp', os.path.join(tar_output_dir, odbc_name, 'lib', 'libmyodbc{}S.so'.format(version['major'])), '/usr/lib'], check_rc=True)
    irods_python_ci_utilities.subprocess_get_output(['sudo', 'cp', os.path.join(tar_output_dir, odbc_name, 'lib', 'libmyodbc{}w.so'.format(version['major'])), '/usr/lib'], check_rc=True)

    # Run the odbc installer
    env_string = 'DRIVER=/usr/lib/libmyodbc{0}w.so;SETUP=/usr/lib/myodbc{0}S.so'.format(version['major'])
    odbc_installer = os.path.join(tar_output_dir, odbc_name, 'bin', 'myodbc-installer')
    driver_version = '.'.join([version['major'], version['minor']])
    for driver_type in ['Unicode', 'ANSI']:
        driver = 'MySQL ODBC {0} {1} Driver'.format(driver_version, driver_type)
        irods_python_ci_utilities.subprocess_get_output(['sudo', odbc_installer, '-d', '-a', '-n', driver, '-t', env_string], check_rc=True)

def configure_client_apt(database):
    if database == 'postgres':
        irods_python_ci_utilities.subprocess_get_output(['apt-get', 'update'], check_rc=True)
        irods_python_ci_utilities.install_os_packages(['postgresql-client', 'odbc-postgresql', 'unixodbc', 'super'])
    elif database == 'mysql':
        #pass
        irods_python_ci_utilities.subprocess_get_output(['apt-get', 'update'], check_rc=True)
        irods_python_ci_utilities.install_os_packages(['mysql-client', 'libpcre3-dev', 'libmysqlclient-dev', 'build-essential', 'libtool', 'autoconf', 'unixodbc'])
        extract_mysql_odbc_connector()
    elif database == 'oracle':
        install_oracle_dependencies()
        install_oracle_client()

def configure_client_yum(database):
    if database == 'postgres':
        irods_python_ci_utilities.install_os_packages(['postgresql-odbc', 'unixODBC', 'unixODBC-devel', 'super'])
    elif database == 'mysql' or database == 'mariadb':
        irods_python_ci_utilities.install_os_packages(['unixODBC', 'unixODBC-devel', 'super'])
    elif database == 'oracle':
        install_oracle_dependencies()
        install_oracle_client()

def configure_client_zypper(database):
    print("not yet implemented")

def configure_client(database):
    dispatch_map = {
        'Ubuntu': configure_client_apt,
        'Centos': configure_client_yum,
        'Centos linux': configure_client_yum,
        'Opensuse': configure_client_zypper,
    }

    try:
        return dispatch_map[irods_python_ci_utilities.get_distribution()](database)
    except KeyError:
        irods_python_ci_utilities.raise_not_implemented_for_distribution()

def install_oracle_dependencies():
    dispatch_map = {
        'Ubuntu': install_oracle_dependencies_apt,
        'Centos': install_oracle_dependencies_yum,
        'Centos linux': install_oracle_dependencies_yum,
    }

    try:
        return dispatch_map[irods_python_ci_utilities.get_distribution()]()
    except KeyError:
        irods_python_ci_utilities.raise_not_implemented_for_distribution()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--database_type', default='postgres', help='database type', required=True)
    args = parser.parse_args()

    database_type = args.database_type    
    configure_client(database_type)
    
if __name__ == '__main__':
    main()
