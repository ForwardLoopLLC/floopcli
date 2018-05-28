import pytest

import json

from copy import copy
from os import remove, environ, mkdir
from os.path import abspath, dirname, isfile, isdir

from shutil import rmtree, which
from typing import Dict

from floopcli.config import _FLOOP_CONFIG_DEFAULT_CONFIGURATION
from floopcli.util.syscall import syscall

FLOOP_TEST_CONFIG_FILE = './floop.json' 

FLOOP_TEST_CONFIG = _FLOOP_CONFIG_DEFAULT_CONFIGURATION

_TEST_FLOOP_CLOUD_CORES = environ.get('FLOOP_CLOUD_CORES')

_TEST_CORE_NAME = 'core0' 
if _TEST_FLOOP_CLOUD_CORES is not None:
    _TEST_CORE_NAME = _TEST_FLOOP_CLOUD_CORES.split(':')[0]

_DEVICE_TEST_SRC_DIRECTORY = '{}/src/'.format(dirname(
    abspath(__file__))
    )

@pytest.fixture(scope='module')
def fixture_docker_machine_bin():
    return which('docker-machine') 

@pytest.fixture(scope='module')
def fixture_rsync_bin():
    return which('rsync') 

@pytest.fixture(scope='function')
def fixture_default_config_file(request):
    config_file = FLOOP_TEST_CONFIG_FILE
    config = FLOOP_TEST_CONFIG
    def cleanup() -> None:
        if isfile(config_file):
            remove(config_file)
    cleanup()
    with open(config_file, 'w') as cf:
        json.dump(config, cf)
    request.addfinalizer(cleanup)
    return config_file

# keep these fixtures separate to allow for fine-grained
# refactoring using different env variables

@pytest.fixture(autouse=True)
def fixture_valid_docker_machine() -> None:
    if environ.get('FLOOP_LOCAL_HARDWARE_TEST'):
        pass
    elif environ.get('FLOOP_CLOUD_TEST'):
        pass
    # default to local 1GB Virtualbox machine
    else: 
        create_local_machine = '''docker-machine create 
        --driver virtualbox 
        --virtualbox-memory 1024
        {}'''.format(_TEST_CORE_NAME)
        syscall(create_local_machine, check=False)

@pytest.fixture(scope='function')
def fixture_valid_target_directory():
    if environ.get('FLOOP_LOCAL_HARDWARE_TEST'):
        return ''
    elif environ.get('FLOOP_CLOUD_TEST'):
        return '/home/ubuntu/floop'
    else: 
        return '/home/floop/floop'

@pytest.fixture(scope='function')
def fixture_valid_core_config(request) -> Dict[str, str]:
    if environ.get('FLOOP_LOCAL_HARDWARE_TEST'):
        return {}
    elif environ.get('FLOOP_CLOUD_TEST'):
        return {'address' : '192.168.1.100',
                'port' : '22',
                'target_source' : fixture_valid_target_directory(), 
                'group' : 'group0',
                'host_docker_machine_bin' : fixture_docker_machine_bin(), 
                'host_key' :  '~/.ssh/id_rsa', 
                'host_rsync_bin' : fixture_rsync_bin(),
                'host_source' : fixture_valid_src_directory(request),
                'core' : _TEST_CORE_NAME,
                'user' : 'floop'}
    else: 
        return {'address' : '192.168.1.100',
                'port' : '22',
                'target_source' : fixture_valid_target_directory(), 
                'group' : 'group0',
                'host_docker_machine_bin' : fixture_docker_machine_bin(), 
                'host_key' :  '~/.ssh/id_rsa', 
                'host_rsync_bin' : fixture_rsync_bin(),
                'host_source' : fixture_valid_src_directory(request),
                'core' : _TEST_CORE_NAME, 
                'user' : 'floop'}


@pytest.fixture(scope='function')
def fixture_invalid_core_core_config(request) -> Dict[str, str]:
    config = fixture_valid_core_config(request)
    config['core'] = 'thisshouldfail'
    return config

@pytest.fixture(scope='function')
def fixture_valid_config_file(request):
    if environ.get('FLOOP_LOCAL_HARDWARE_TEST'):
        return ''
    elif environ.get('FLOOP_CLOUD_TEST') is not None:
        cloud_cores = environ['FLOOP_CLOUD_CORES'].split(':')
        src_dir = fixture_valid_src_directory(request)
        config_file = fixture_default_config_file(request)
        with open(config_file, 'r') as cf:
            data = json.load(cf)
        data['groups']['group0']['cores']['default']['host_source'] = src_dir
        del data['groups']['group0']['cores']['core0']
        for idx, core in enumerate(cloud_cores):
            data['groups']['group0']['cores'][core] = {
                'address' : '192.168.1.' + str(idx),
                'port' : '22',
                'target_source' : '/home/ubuntu/floop',
                'user' : 'floop',
                'host_key' : '~/.ssh/id_rsa'
            }
        with open(config_file, 'w') as cf:
            json.dump(data, cf)
        return config_file
    else: 
        src_dir = fixture_valid_src_directory(request)
        config_file = fixture_default_config_file(request)
        with open(config_file, 'r') as cf:
            data = json.load(cf)
        data['groups']['group0']['cores']['default']['host_source'] = src_dir
        with open(config_file, 'w') as cf:
            json.dump(data, cf)
        return config_file

#
#

@pytest.fixture(scope='function')
def fixture_malformed_config_file(request):
    config_file = fixture_valid_config_file(request)
    with open(config_file, 'r') as cf:
        data = json.load(cf)
    data['groups'] = {}
    with open(config_file, 'w') as cf:
        json.dump(data, cf)
    return config_file

@pytest.fixture(scope='function')
def fixture_invalid_core_config_file(request):
    config_file = fixture_valid_config_file(request)
    with open(config_file, 'r') as cf:
        data = json.load(cf)
    cores = data['groups']['group0']['cores'].keys()
    core = [c for c in cores if c != 'default'][0]
    core_config = data['groups']['group0']['cores'][core]
    for c in list(cores):
        if c != 'default':
            del data['groups']['group0']['cores'][c]
    data['groups']['group0']['cores']['thisshouldnotwork'] = core_config 
    with open(config_file, 'w') as cf:
        json.dump(data, cf)
    return config_file



@pytest.fixture(scope='function')
def fixture_incomplete_config_file(request):
    config_file = fixture_valid_config_file(request)
    with open(config_file, 'r') as cf:
        data = json.load(cf)
    data['groups'] = {
            'default' : {},
            'group0' : {
                'cores' : {
                    'default' : {},
                    'core0' : {},
                }
            }
        }
    with open(config_file, 'w') as cf:
        json.dump(data, cf)
    return config_file

@pytest.fixture(scope='function')
def fixture_valid_src_directory(request):
    src_dir = _DEVICE_TEST_SRC_DIRECTORY 
    if isdir(src_dir):
        rmtree(src_dir)
    mkdir(src_dir)
    def cleanup() -> None:
        if isdir(src_dir):
            rmtree(src_dir)
    request.addfinalizer(cleanup)
    return src_dir

@pytest.fixture(scope='function')
def fixture_buildfile(request):
    src_dir = fixture_valid_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
RUN sh''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_buildfile(request):
    src_dir = fixture_valid_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
RUN apt-get update''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_runfile(request):
    src_dir = fixture_valid_src_directory(request)
    buildfile = '{}/Dockerfile'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
CMD ["apt-get", "update"]''' 
    with open(buildfile, 'w') as bf:
        bf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_testfile(request):
    src_dir = fixture_valid_src_directory(request)
    testfile = '{}/Dockerfile.test'.format(_DEVICE_TEST_SRC_DIRECTORY)
    testfile_contents = '''FROM busybox:latest
run sh''' 
    with open(testfile, 'w') as tf:
        tf.write(testfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_failing_testfile(request):
    src_dir = fixture_valid_src_directory(request)
    buildfile = '{}/Dockerfile.test'.format(_DEVICE_TEST_SRC_DIRECTORY)
    buildfile_contents = '''FROM busybox:latest
CMD ["apt-get", "update"]''' 
    with open(buildfile, 'w') as tf:
        tf.write(buildfile_contents)
    return src_dir

@pytest.fixture(scope='function')
def fixture_redundant_config_file(request):
    config_file = fixture_valid_config_file(request)
    with open(config_file, 'r') as cf:
        data = json.load(cf)
    core = [k for k in data['groups']['group0']['cores'].keys() if k != 'default'][0]
    core_config = data['groups']['group0']['cores'][core]
    default_config = data['groups']['group0']['cores']['default']
    data['groups']['group0']['cores'] = {
            'default' : default_config, 
            'core0' : core_config, 'core1' : core_config}
    with open(config_file, 'w') as cf:
        json.dump(data, cf)
    return config_file

@pytest.fixture(scope='function')
def fixture_missing_property_config_file(request):
    config_file = fixture_valid_config_file(request)
    with open(config_file, 'r') as cf:
        data = json.load(cf)
    core_config = data['groups']['group0']['cores'][_TEST_CORE_NAME]
    del core_config['user']
    default_config = data['groups']['group0']['cores']['default']
    data['groups']['group0']['cores'] = {
            'default' : default_config, 
            _TEST_CORE_NAME : core_config}
    with open(config_file, 'w') as cf:
        json.dump(data, cf)
    return config_file

@pytest.fixture(scope='function')
def fixture_nonexistent_source_dir_config(request):
    test_config = fixture_valid_core_config(request)
    test_config['host_source'] = \
            'definitely/not/a/real/directory/'
    return test_config 

@pytest.fixture(scope='function')
def fixture_nonexistent_source_dir_cli_config_file(request):
    config_file = fixture_valid_config_file(request)
    with open(config_file, 'r') as cf:
        data = json.load(cf)
    data['groups']['group0']['cores']['default']['host_source'] =\
            'definitely/not/a/real/src/dir/'
    with open(config_file, 'w') as cf:
        json.dump(data, cf)
    return config_file 

@pytest.fixture(scope='function')
def fixture_protected_target_directory_config(request):
    test_config = fixture_valid_core_config(request)
    test_config['target_source'] = '/.test/' 
    return test_config 

@pytest.fixture(scope='function')
def fixture_docker_machine_wrapper(request):
    def wrapper() -> None:
        fixture_valid_docker_machine()
    return wrapper
