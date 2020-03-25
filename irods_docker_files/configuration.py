os_identifier_dict = {
    'centos_7': 'centos:7',
    'ubuntu_14': 'ubuntu:14.04',
    'ubuntu_16': 'ubuntu:16.04',
    'ubuntu_18': 'ubuntu:18.04'
}

platform_dockerfile_map = {
    'centos_7' : 'Dockerfile.centos',
    'ubuntu_16' : 'Dockerfile.ubuntu'
}

database_dict = {
    'mariadb': 'mariadb:10.1',
    'mysql': 'mysql:5.7',
    'postgres': 'postgres:12.1'
}

docker_client_base_url = 'unix://var/run/docker.sock'

