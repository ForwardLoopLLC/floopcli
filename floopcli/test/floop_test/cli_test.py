import pytest
import json
from copy import copy

from os import remove
from os.path import isfile
from itertools import combinations

from floopcli.util.syscall import syscall, SystemCallException
from floopcli.test.fixture import * 

@pytest.fixture(scope='function')
def fixture_unknown_cli_commands():
    return [
            'notactuallyacommand',
            'not actuallyacommand',
            'not actually acommand',
            'not actually a command',
            'n o t a c t u a l l y a c o m m a n d'
            ]

@pytest.fixture(scope='function')
def fixture_cli_base(request):
    return ['floop', 'floop -c floop.json']

@pytest.fixture(scope='function')
def fixture_cli_base_nonexistent_config_file():
    return 'floop -c definitelynotarealconfigfile.json' 

@pytest.fixture(scope='module')
def fixture_supported_cli_commands():
    return {
            'create' : ['-v'],
            'ps' : ['-v'],
            'push' : ['-v'],
            'build' : ['-v'],
            'run' : ['-v'],
            'logs' : ['-v'],
            'test' : ['-v']
            }

@pytest.fixture(scope='function')
def fixture_incompatible_cli_commands():
    return [
            'floop -c floop.json config'
            ]

@pytest.fixture(scope='function')
def fixture_malformed_floop_configs(request):
    test_config_file = fixture_valid_config_file(request)
    with open(test_config_file) as tcf:
        valid_config = json.load(tcf)
    config_files = ['malformed-config-{}.json'.format(key) for key
            in sorted(valid_config.keys())]
    def cleanup():
        for cf in config_files:
            if isfile(cf):
                remove(cf)
    cleanup()
    request.addfinalizer(cleanup)
    for idx, key in enumerate(sorted(valid_config.keys())):
        config = copy(valid_config)
        del config[key]
        config_file = config_files[idx]
        with open(config_file, 'w') as cf:
            json.dump(config, cf)
    return config_files

def test_cli_build_fail_fails(fixture_valid_config_file, fixture_failing_buildfile):
    with pytest.raises(SystemCallException):
        syscall(
            'floop -c {} build'.format(
                fixture_valid_config_file), check=True)

def test_cli_run_fail_fails(fixture_valid_config_file, fixture_failing_runfile):
    with pytest.raises(SystemCallException):
        syscall(
            'floop -c {} run'.format(
                fixture_valid_config_file), check=True)

def test_cli_test_fail_fails(fixture_valid_config_file, fixture_failing_testfile):
    with pytest.raises(SystemCallException):
        syscall(
            'floop -c {} test'.format(
                fixture_valid_config_file), check=True)

def test_cli_push_nonexistent_src_dir_fails(fixture_nonexistent_source_dir_cli_config_file):
    with pytest.raises(SystemCallException):
        syscall(
            'floop -c {} push'.format(
                fixture_nonexistent_source_dir_cli_config_file), check=True)

def test_cli_push_redundant_config_fails(fixture_redundant_config_file):
    with pytest.raises(SystemCallException):
        syscall(
            'floop -c {} push'.format(
                fixture_redundant_config_file), check=True)
def test_cli_version():
    syscall('floop --version', check=True)

def test_cli_bases_fail(fixture_cli_base, fixture_valid_config_file):
    for base in fixture_cli_base:
        with pytest.raises(SystemCallException):
            syscall(base, check=True)

def test_cli_commands_malformed_configs_fails(fixture_malformed_floop_configs, fixture_supported_cli_commands):
    for config in fixture_malformed_floop_configs:
        for command in fixture_supported_cli_commands.keys():
            with pytest.raises(SystemCallException):
                syscall('floop -c {} {}'.format(
                    config, command), check=True)

def test_cli_commands_nonexistent_config_fails(fixture_cli_base_nonexistent_config_file, fixture_supported_cli_commands):
    for command in fixture_supported_cli_commands.keys():
        with pytest.raises(SystemCallException):
            syscall('{} {}'.format(
                fixture_cli_base_nonexistent_config_file, command), check=True)

def test_incompatible_cli_commands_fail(fixture_incompatible_cli_commands):
    for command in fixture_incompatible_cli_commands:
        with pytest.raises(SystemCallException):
            syscall(command, check=True)

def test_cli_unknown_commands_fail(fixture_cli_base, fixture_valid_config_file, fixture_unknown_cli_commands):
    for base in fixture_cli_base:
        for command in fixture_unknown_cli_commands:
            with pytest.raises(SystemCallException):
                syscall('{} {}'.format(base, command), check=True)


class TestConfig():
    '''
    Config does not act on cores, so separate tests from core-bound methods
    '''
    def test_cli_config_overwrite(fixture_cleanup_config):
        syscall('floop config', check=True)
        syscall('floop config', check=True)
        syscall('floop config --overwrite', check=True)

class TestCreate():
    def test_cli_create(self, fixture_cli_base, fixture_valid_config_file):
        for base in fixture_cli_base:
            syscall('{} create --timeout 10'.format(base), check=True)

    def test_cli_create_nonexistent_config_file_fails(self):
        with pytest.raises(SystemCallException):
            syscall('floop create', check=True)
        with pytest.raises(SystemCallException):
            syscall('floop create -v', check=True)

class TestPS():
    def test_cli_ps(self, fixture_cli_base, fixture_valid_config_file):
        for base in fixture_cli_base:
            syscall('{} ps'.format(base), check=True)
            syscall('{} ps -v'.format(base), check=True)

    def test_cli_ps_nonexistent_config_file_fails(self):
        with pytest.raises(SystemCallException):
            syscall('floop ps', check=True)
        with pytest.raises(SystemCallException):
            syscall('floop ps -v', check=True)

class TestLogs():
    def test_cli_logs(self, fixture_cli_base, fixture_valid_config_file):
        syscall('floop logs', check=True)
        syscall('floop logs -m test', check=True)
        syscall('floop logs -v', check=True)
        syscall('floop logs -v -m test', check=True)

    def test_cli_logs_incompatible_flags(self):
        with pytest.raises(SystemCallException):
            syscall('floop -c floop.json logs', check=True)

class TestPush():
    def test_cli_push(self, fixture_cli_base, fixture_valid_config_file):
        for base in fixture_cli_base:
            syscall('{} push'.format(base), check=True)
            syscall('{} push -v'.format(base), check=True)

    def test_cli_push_nonexistent_config_file_fails(self):
        with pytest.raises(SystemCallException):
            syscall('floop push', check=True)
        with pytest.raises(SystemCallException):
            syscall('floop push -v', check=True)

class TestBuild():
    def test_cli_build(self, fixture_cli_base,
            fixture_valid_config_file,
            fixture_buildfile):
        for base in fixture_cli_base:
            syscall('{} build'.format(base), check=True)
            syscall('{} build -v'.format(base), check=True)

    def test_cli_build_nonexistent_config_file_fails(self, fixture_cli_base):
        for base in fixture_cli_base:
            with pytest.raises(SystemCallException):
                syscall('{} build'.format(base), check=True)
            with pytest.raises(SystemCallException):
                syscall('{} build -v'.format(base), check=True)

class TestRun():
    def test_cli_run(self, fixture_cli_base,
            fixture_valid_config_file,
            fixture_buildfile):
        for base in fixture_cli_base:
            syscall('{} run'.format(base), check=True)
            syscall('{} run -v'.format(base), check=True)

    def test_cli_run_nonexistent_config_file_fails(self, fixture_cli_base):
        for base in fixture_cli_base:
            with pytest.raises(SystemCallException):
                syscall('{} run'.format(base), check=True)
            with pytest.raises(SystemCallException):
                syscall('{} run -v'.format(base), check=True)

class TestTest():
    def test_cli_test(self, fixture_cli_base,
            fixture_valid_config_file,
            fixture_testfile):
        for base in fixture_cli_base:
            syscall('{} test'.format(base), check=True)
            syscall('{} test -v'.format(base), check=True)

    def test_cli_test_nonexistent_config_file_fails(self, fixture_cli_base):
        for base in fixture_cli_base:
            with pytest.raises(SystemCallException):
                syscall('{} test'.format(base), check=True)
            with pytest.raises(SystemCallException):
                syscall('{} test -v'.format(base), check=True)

class TestDestroy():
    #@pytest.mark.last
    #def test_cli_destroy(self, fixture_cli_base,
    #        fixture_valid_config_file,
    #        fixture_docker_machine_wrapper):
    #    enforce_docker_machine = fixture_docker_machine_wrapper
    #    for base in fixture_cli_base[-1:]:
    #        print(base)
    #        enforce_docker_machine()
    #        out = syscall('{} destroy -v'.format(base), check=True)
    #        print(out)

    def test_cli_destroy_nonexistent_core_is_idempotent(self,
            fixture_cli_base, fixture_invalid_core_config_file):
        syscall('floop destroy', check=True)
        syscall('floop destroy', check=True)

    def test_cli_destroy_nonexistent_config_file_fails(self, fixture_cli_base):
        with pytest.raises(SystemCallException):
            for base in fixture_cli_base:
                syscall('{} destroy'.format(base), check=True)
        with pytest.raises(SystemCallException):
            for base in fixture_cli_base:
                syscall('{} destroy -v'.format(base), check=True)
