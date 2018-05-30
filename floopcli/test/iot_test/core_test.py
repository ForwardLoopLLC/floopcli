import pytest
import os
import os.path
import json
from shutil import rmtree, which
from copy import copy
from floopcli.util.syscall import syscall
from floopcli.test.fixture import *
from floopcli.iot.core import create, build, run, push, ps, test, destroy, \
        Core, CoreCreateException, CannotSetImmutableAttribute, \
        SSHKeyNotFound, \
        CoreSourceNotFound, \
        CoreCommunicationException, \
        CoreBuildFileNotFound, \
        CoreBuildException, \
        CoreRunException, \
        CoreTestException, \
        CoreTestFileNotFound

@pytest.fixture(scope='function')
def fixture_valid_core(request):
    valid_config = fixture_valid_core_config(request)
    core = Core(**valid_config)
    create(core, check=True)
    return core

def test_core_init(fixture_docker_machine_bin, fixture_valid_core_config):
    core = Core(**fixture_valid_core_config)

def test_core_nonexistent_src_dir_fails(fixture_nonexistent_source_dir_config):
    with pytest.raises(CoreSourceNotFound):
        Core(**fixture_nonexistent_source_dir_config)

def test_core_init_nonexistent_ssh_key_fails(fixture_valid_core_config):
    config = fixture_valid_core_config
    config['host_key'] = '/definitely/not/a/valid/ssh/key'
    with pytest.raises(SSHKeyNotFound):
        Core(**fixture_valid_core_config)

def test_core_set_attributes_after_init_fails(fixture_valid_core_config):
    core = Core(**fixture_valid_core_config)
    for key in fixture_valid_core_config.keys():
        with pytest.raises(CannotSetImmutableAttribute):
            setattr(core, key, fixture_valid_core_config[key])

def test_core_create_invalid_core_fails(fixture_invalid_core_core_config):
    core = Core(**fixture_invalid_core_core_config)
    with pytest.raises(CoreCreateException):
        create(core)

def test_core_run_ssh_command_pwd(fixture_valid_core):
    fixture_valid_core.run_ssh_command(command='pwd', check=True)

def test_core_push(fixture_valid_core):
    push(fixture_valid_core)

def test_core_push_protected_target_dir_fails(fixture_protected_target_directory_config):
    core = Core(**fixture_protected_target_directory_config)
    create(core)
    with pytest.raises(CoreCommunicationException):
        push(core)

def test_core_build(fixture_valid_core, fixture_buildfile):
    build(fixture_valid_core)

def test_core_build_no_buildfile_fails(fixture_valid_core, 
        fixture_valid_src_directory, fixture_valid_target_directory):
    with pytest.raises(CoreBuildFileNotFound):
        build(fixture_valid_core)

def test_core_build_docker_build_fail_fails(fixture_valid_core, 
        fixture_failing_buildfile, fixture_valid_target_directory):
    with pytest.raises(CoreBuildException):
        build(fixture_valid_core)

def test_core_run(fixture_valid_core, 
        fixture_buildfile, fixture_valid_target_directory):
    run(fixture_valid_core)

def test_core_run_docker_run_fail_fails(fixture_valid_core, 
        fixture_failing_runfile, fixture_valid_target_directory):
    with pytest.raises(CoreRunException):
        run(fixture_valid_core)

def test_core_ps(fixture_valid_core):
    ps(fixture_valid_core)

def test_core_test(fixture_valid_core, 
        fixture_testfile, fixture_valid_target_directory):
    test(fixture_valid_core)

def test_core_test_nonexistent_testfile_fails(fixture_valid_core, 
        fixture_buildfile, fixture_valid_target_directory):
    with pytest.raises(CoreTestFileNotFound):
        test(fixture_valid_core)

def test_core_test_docker_test_fail_fails(fixture_valid_core, 
        fixture_failing_testfile, fixture_valid_target_directory):
    with pytest.raises(CoreTestException):
        test(fixture_valid_core)

def test_core_destroy(fixture_valid_core, fixture_valid_target_directory):
    destroy(fixture_valid_core)
