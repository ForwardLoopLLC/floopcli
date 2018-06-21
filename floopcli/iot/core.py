import logging
import sys
import os
import signal

from os.path import isfile, isdir, expanduser
from subprocess import check_output
from typing import TypeVar, List

from floopcli.util.syscall import syscall, SystemCallException

logger = logging.getLogger(__name__)

def verbose(): # type: () -> bool
    '''
    Check whether verbose mode is enabled

    Returns:
        bool:
            if True, verbose is enabled
    '''
    return 'console' in [h.name for h in logging.getLogger().handlers[:]] #type: ignore

class CannotSetImmutableAttribute(Exception):
    '''
    Tried to set immutable attribute after initialization
    '''
    pass

class SSHKeyNotFound(Exception):
    '''
    Specified SSH private key file does not exist
    '''
    pass

class CoreCreateException(Exception):
    '''
    Non-zero exit code while creating new Docker machine
    '''
    pass

class DockerMachineBinaryNotFound(Exception):
    '''
    Specified docker-machine binary does not exist
    '''
    pass

class CoreSourceNotFound(Exception):
    '''
    Specified target source code directory does not exist
    '''
    pass

class CoreBuildFileNotFound(Exception):
    '''
    Host source code has no Dockerfile
    '''
    pass

class CoreTestFileNotFound(Exception):
    '''
    Host source code has no Dockerfile.test
    '''
    pass

class CoreCommunicationException(Exception):
    '''
    Cannot communicate with core via docker-machine SSH
    '''
    pass

class CoreBuildException(Exception):
    '''
    Target core build command returned non-zero exit code
    '''
    pass
class CoreRunException(Exception):
    '''
    Target core run command returned non-zero exit code
    '''
    pass

class CoreTestException(Exception):
    '''
    Target core test command returned non-zero exit code
    '''
    pass

class CoreDestroyException(Exception):
    '''
    Target core destroy command returned non-zero exit code
    '''
    pass

class CorePSException(Exception):
    '''
    Target core ps command returned non-zero exit code
    '''
    pass

CoreType = TypeVar('CoreType', bound='Core')
'''Generic self core type'''

class Core(object):
    '''
    Handles initializing and interacting with a target core

    All attributes are immutable. If you try to set an instance
    attribute after initialize, it will raise :py:class:`CannotSetImmutableAttribute`
    '''
    def __init__(self,
            address,
            port,
            target_source,
            group,
            host_docker_machine_bin,
            host_key,
            host_network,
            host_rsync_bin,
            host_source,
            build_file,
            test_file,
            privileged,
            docker_socket,
            hardware_devices,
            core,
            user,
            **kwargs): 
        # type: (CoreType, str, str, str, str, str, str, str, str, str, str, str, bool, str, str, str, str) -> None

        self.address = address
        '''Core IP address (reachable by SSH)'''
        self.port = port
        '''Core SSH port'''
        self.target_source = target_source
        '''Directory on the target operating system to store files'''
        self.group = group
        '''Core group core'''
        self.host_docker_machine_bin = host_docker_machine_bin
        '''Path on host to docker-machine binary'''
        self.host_key = host_key
        '''Path on host to SSH key that works for user'''
        self.host_network = host_network
        '''Flag to use core host network'''
        self.host_rsync_bin = host_rsync_bin
        '''Path on host to rsync binary'''
        self.host_source = host_source
        '''Path on host to source file directory'''
        self.build_file = build_file
        '''Relative path to build file from host_source'''
        self.test_file = test_file
        '''Relative path to test file from host_source'''
        self.privileged = privileged
        '''Flag to allow privileged container access on core'''
        self.docker_socket = docker_socket
        '''Path to core Docker socket'''
        self.hardware_devices = hardware_devices
        '''Hardware devices to expose to core Docker'''
        self.core = core.replace(' ','').replace('-','')
        '''Core name (must match Docker machine core, if machine already exists)
        During initialization, all machine cores will have spaces and -'s removed
        '''
        self.user = user
        '''Core SSH user on the target'''

    @property
    def address(self): # type: (CoreType) -> str
        return self.__address

    @address.setter
    def address(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'address'):
            raise CannotSetImmutableAttribute('address')
        self.__address = value

    @property
    def port(self): # type: (CoreType) -> str
        return self.__port

    @port.setter
    def port(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'port'):
            raise CannotSetImmutableAttribute('port')
        self.__port = value

    @property
    def target_source(self): # type: (CoreType) -> str
        return self.__target_source

    @target_source.setter
    def target_source(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'target_source'):
            raise CannotSetImmutableAttribute('target_source')
        self.__target_source = value

    @property
    def group(self): # type: (CoreType) -> str
        return self.__group

    @group.setter
    def group(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'group'):
            raise CannotSetImmutableAttribute('group')
        self.__group = value

    @property
    def host_docker_machine_bin(self): # type: (CoreType) -> str
        return self.__host_docker_machine_bin

    @host_docker_machine_bin.setter
    def host_docker_machine_bin(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'host_docker_machine_bin'):
            raise CannotSetImmutableAttribute('host_docker_machine_bin')
        self.__host_docker_machine_bin = value

    @property
    def host_key(self): # type: (CoreType) -> str
        return self.__host_key

    @host_key.setter
    def host_key(self, value): # type: (CoreType, str) -> None
        '''
        SSH key setter

        Args:
            value (str):
                path of SSH private key for core
        Raises:
            :py:class:`floopcli.iot.core.SSHKeyNotFound`:
                SSH private key file does not exist
            :py:class:`floopcli.iot.core.CannotSetImmutableAttribute`:
                attempting to modify the host_key attribute after initialization will fail
        '''
        value = expanduser(value)
        if hasattr(self, 'host_key'):
            raise CannotSetImmutableAttribute('host_key')
        if not isfile(value) or value is None:
            raise SSHKeyNotFound(value)
        self.__host_key = value

    @property
    def host_network(self): # type: (CoreType) -> bool 
        return self.__host_network

    @host_network.setter
    def host_network(self, value): # type: (CoreType, bool) -> None
        if hasattr(self, 'host_network'):
            raise CannotSetImmutableAttribute('host_network')
        self.__host_network = value

    @property
    def privileged(self): # type: (CoreType) -> bool 
        return self.__privileged

    @privileged.setter
    def privileged(self, value): # type: (CoreType, bool) -> None
        if hasattr(self, 'privileged'):
            raise CannotSetImmutableAttribute('privileged')
        self.__privileged = value

    @property
    def host_rsync_bin(self): # type: (CoreType) -> str
        return self.__host_rsync_bin

    @host_rsync_bin.setter
    def host_rsync_bin(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'host_rsync_bin'):
            raise CannotSetImmutableAttribute('host_rsync_bin')
        self.__host_rsync_bin = value

    @property
    def docker_socket(self): # type: (CoreType) -> str
        return self.__docker_socket

    @docker_socket.setter
    def docker_socket(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'docker_socket'):
            raise CannotSetImmutableAttribute('docker_socket')
        self.__docker_socket = value

    @property
    def hardware_devices(self): # type: (CoreType) -> List[str]
        return self.__hardware_devices

    @hardware_devices.setter
    def hardware_devices(self, value): # type: (CoreType, List[str]) -> None
        if hasattr(self, 'hardware_devices'):
            raise CannotSetImmutableAttribute('hardware_devices')
        self.__hardware_devices = value

    @property
    def host_source(self): # type: (CoreType) -> str
        return self.__host_source

    @host_source.setter
    def host_source(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'host_source'):
            raise CannotSetImmutableAttribute('host_source')
        if not isdir(value):
            raise CoreSourceNotFound(value)
        self.__host_source = value

    @property
    def build_file(self): # type: (CoreType) -> str
        return self.__build_file

    @build_file.setter
    def build_file(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'build_file'):
            raise CannotSetImmutableAttribute('build_file')
        self.__build_file = value 

    @property
    def test_file(self): # type: (CoreType) -> str
        return self.__test_file

    @test_file.setter
    def test_file(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'test_file'):
            raise CannotSetImmutableAttribute('test_file')
        self.__test_file = value 

    @property
    def core(self): # type: (CoreType) -> str
        return self.__core

    @core.setter
    def core(self, value): # type: (CoreType, str) -> None
        if hasattr(self, 'core'):
            raise CannotSetImmutableAttribute('core')
        self.__core = value

    @property
    def user(self): # type: (CoreType) -> str
        return self.__user

    @user.setter
    def user(self, value): # type: (CoreType, str) -> None
        '''
        SSH user setter

        Args:
            value (str):
                core of SSH user for core
        Raises:
            :py:class:`floopcli.core.iot.CannotSetImmutableAttribute`:
                attempting to modify the user attribute after initialization will fail
        '''

        if not hasattr(self, 'user'):
            self.__user = value
        else:
            raise CannotSetImmutableAttribute('user')

    def run_ssh_command(self,
            command,
            check=True,
            verbose=False): # type: (CoreType, str, bool, bool) -> str
        '''
        Run docker-machine SSH command on target core

        Args:
            command (str):
                command to run on target core
            check (bool):
                if True, check whether command exit code is non-zero
        Returns:
            str:
                stdout output of SSH command
        Raises:
            :py:class:`floopcli.util.syscall.SystemCallException`:
                SSH command exit code was non-zero
        '''
        sys_string = '{} ssh {} {}'.format(
            self.host_docker_machine_bin, self.core, command)
        out, _ = syscall(sys_string, check=check, verbose=verbose)
        return out

def __log(core, level, message): # type: (Core, str, str) -> None
    '''
    Log message about core to default logger

    Automatically prepends calling function core to
    log output

    Args:
        core (:py:class:`floopcli.core.iot.Core`):
            initialized target core object
        level (str):
            logger logging level (only use 'info' or 'error')
        message (str):
            message to log
    '''
    if hasattr(logger, level):
        for line in message.split('\n'):
            line = '{} (target) - {}: {}'.format(
                    core.core,
                    sys._getframe(1).f_code.co_name,
                    line)
            getattr(logger, level)(line)

###  parallelizable methods that act on Core objects
# these functions are pickle-able, but class methods are NOT
# so these functions can be passed to multiprocessing.Pool
def create(core, check=True, timeout=240): # type: (Core, bool, int) -> None
    '''
    Parallelizable; create new docker-machine on target core

    Args:
        core (:py:class:`floopcli.core.iot.Core`):
            initialized target core object
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
        timeout (int):
            time in seconds to wait for success before throwing error
            (docker-machine create timeout is too long)
    Raises:
        :py:class:`floopcli.core.iot.CoreCreateException`:
            core creation failed during docker-machine create or
            'pwd' check failed
    '''
    def timeout_handler(signum, frame): #type: ignore
        raise CoreCreateException('Create core timed out')
    create_command = '{} create --driver generic --generic-ip-address {} --generic-ssh-port {} --generic-ssh-user {} --generic-ssh-key {} --engine-storage-driver overlay {}'.format(
        core.host_docker_machine_bin,
        core.address, 
        core.port,
        core.user, 
        core.host_key, 
        core.core)
    __log(core, 'info', create_command)
    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(timeout)
    try:
        out, err = syscall(create_command, check=False, verbose=verbose())
        __log(core, 'info', out)
        if check:
            check_command = 'pwd'
            __log(core, 'info', 'Checking with {}'.format(check_command))
            outd = core.run_ssh_command('pwd', check=check)
            __log(core, 'info', outd)
    except SystemCallException as e:
        __log(core, 'error', 'Create timed out')
        raise CoreCreateException(repr(e))

def push(core, check=True): # type: (Core, bool) -> None
    '''
    Parallelizable; push files from host to target core 

    Ignores floop.log and floop.json

    Args:
        core (:py:class:`floopcli.core.iot.Core`):
            initialized target core object
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`floopcli.core.iot.CoreCreateException`:
            core creation failed during docker-machine create or
            'pwd' check failed
    '''
    # prevents race condition where source exists at start of floop
    # call but gets removed before push 
    # TODO: simulate the race condition
    if not isdir(core.host_source):
        __log(core, 'error', 'Source not found: {}'.format(core.host_source))
        raise CoreSourceNotFound(core.host_source)
    try:
        mkdir_string = 'mkdir -p {}'.format(core.target_source)
        __log(core, 'info', mkdir_string)
        out = core.run_ssh_command(mkdir_string, check=True)
        __log(core, 'info', out)
        sync_string = "rsync -avhz -e '{} ssh' {} {}:'{}' --exclude=floop.log --exclude=floop.json --delete".format(core.host_docker_machine_bin, core.host_source,
            core.core, core.target_source)
        __log(core, 'info', sync_string)
        out, err = syscall(sync_string, check=check)
        __log(core, 'info', out)
    except SystemCallException as e:
        __log(core, 'error', repr(e))
        raise CoreCommunicationException(repr(e))

def build(core, check=True): # type: (Core, bool) -> None
    '''
    Parallelizable; push then build files from host on target core 

    Args:
        core (:py:class:`floopcli.core.iot.Core`):
            initialized target core object
            
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`floopcli.iot.core.CoreBuildFileNotFound`:
            no Dockerfile in source code directory on host
        :py:class:`floopcli.iot.core.CoreBuildException`:
            build commands returned non-zero exit code
    '''

    host_build_file = '{}/{}'.format(core.host_source, core.build_file)
    if not isfile(host_build_file) or core.build_file is None:
        __log(core, 'error', 'Core build file not found: {}'.format(host_build_file))
        raise CoreBuildFileNotFound(host_build_file)
    target_build_file = '{}/{}'.format(core.target_source, core.build_file)
    push(core)
    meta_build_command = 'docker build -f {} -t floop {}/'.format(
            target_build_file, core.target_source)
    __log(core, 'info', meta_build_command)
    try:
        out = core.run_ssh_command(meta_build_command, check=check, verbose=verbose())
        __log(core, 'info', out)
    except (SystemCallException, CoreBuildException) as e:
        __log(core, 'error', repr(e))
        raise CoreBuildException(repr(e))

def run(core, check=True): # type: (Core, bool) -> None
    '''
    Parallelizable; push, build, then run files from host on target core 

    Args:
        core (:py:class:`floopcli.iot.core.Core`):
            initialized target core object
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`floopcli.iot.core.CoreCommunicationException`:
            could not communicate from host to core to remove runtime container
        :py:class:`floopcli.iot.core.CoreRunException`:
            run commands returned non-zero exit code
    '''

    build(core)
    rm_command = 'docker rm -f floop || true'
    __log(core, 'info', rm_command)
    try:
        out = core.run_ssh_command(command=rm_command, check=check, verbose=verbose())
        __log(core, 'info', out)
        run_command = 'docker run --name floop -v {}:/floop/'.format(
                core.target_source)
        if core.privileged:
            run_command = '{} --privileged'.format(run_command)
            if core.docker_socket != '':
                run_command = '{} -v {}:/var/run/docker.sock'.format(
                        run_command, core.docker_socket)
            if core.host_network:
                run_command = '{} --network host'.format(run_command)
        for device in core.hardware_devices:
            run_command = '{} --device {}'.format(run_command, device)
        run_command = '{} floop'.format(run_command)
        __log(core, 'info', run_command)
        out = core.run_ssh_command(command=run_command, check=check, verbose=verbose())
        __log(core, 'info', out)
    except SystemCallException as e:
        __log(core, 'error', repr(e))
        raise CoreRunException(repr(e))

def ps(core, check=True): # type: (Core, bool) -> None
    '''
    Parallelizable; push, build, then run files from host on target core 

    Args:
        core (:py:class:`floopcli.core.iot.Core`):
            initialized target core object
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`floopcli.iot.core.CorePSException`:
            ps commands returned non-zero exit code
    '''

    ps_command = 'docker ps'
    __log(core, 'info', ps_command)
    try:
        out = core.run_ssh_command(ps_command, check=check)
        __log(core, 'info', out)
    # TODO: find a case where core initializes but ps fails
    except SystemCallException as e:
        __log(core, 'error', repr(e))
        raise CorePSException(repr(e))

# need to mangle the name to prevent pytest from erroneously discovering 
def _test(core, check=True): # type: (Core, bool) -> None
    '''
    Parallelizable; push, build, then run test files from host on target core 

    Args:
        core (:py:class:`floopcli.iot.core.Core`):
            initialized target core object
        check (bool):
            if True, check core creation succeeded by running
            'pwd' via docker-machine SSH on newly created core
    Raises:
        :py:class:`floopcli.iot.core.CoreTestFileNotFound`:
            no Dockerfile.test in source code directory on host
        :py:class:`floopcli.iot.core.CoreTestException`:
            test commands returned non-zero exit code
    '''
    host_test_file = '{}/{}'.format(core.host_source, core.test_file)
    if not isfile(host_test_file) or core.test_file is None:
        __log(core, 'error', 'Test file not found: {}'.format(core.test_file))
        raise CoreTestFileNotFound(core.test_file)
    target_test_file = '{}/{}'.format(core.target_source, core.test_file)
    push(core)
    try:
        rm_command = 'docker rm -f flooptest || true'
        __log(core, 'info', rm_command)
        out = core.run_ssh_command(rm_command, check=check, verbose=verbose())
        __log(core, 'info', out)
        test_build_command = 'docker build -f {} -t flooptest {}/'.format(
                target_test_file,
                core.target_source)
        __log(core, 'info', test_build_command)
        out = core.run_ssh_command(test_build_command, check=check, verbose=verbose())
        __log(core, 'info', out)
        test_run_command = 'docker run --name flooptest -v {}:/floop/ flooptest'.format(
                core.target_source)
        __log(core, 'info', test_run_command)
        out = core.run_ssh_command(test_run_command, check=check, verbose=verbose())
        __log(core, 'info', out)
    except SystemCallException as e:
        __log(core, 'error', repr(e))
        raise CoreTestException(repr(e))

def destroy(core, check=True): # type: (Core, bool) -> None
    '''
    Parallelizable; destroy core by rm'ing Docker machine

    Args:
        core (:py:class:`floopcli.iot.core.Core`):
            initialized target core object
        check (bool):
            if True, check that core destroy system calls
            return non-zero exit codes
    Raises:
        :py:class:`floopcli.iot.core.CoreDestroyException`:
            destroy commands returned non-zero exit code
    '''
    try:
        rm_core = ('sys', '{} rm -f {}'.format(
            core.host_docker_machine_bin, core.core))
        # order matters
        commands = [
                rm_core
                ]
        for command_ in commands:
            kind, command = command_
            __log(core, 'info', command)
            if kind =='sys':
                out, err = syscall(command=command, check=check)
                __log(core, 'info', str((out, err)))
    # TODO: find a case where init succeeds but destroy fails, enforce idempotency
    except SystemCallException as e:
        __log(core, 'error', repr(e))
        raise CoreDestroyException(repr(e))
