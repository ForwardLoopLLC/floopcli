import argparse
import json
import logging

from functools import partial
from multiprocessing import Pool
from os import makedirs, remove 
from os.path import isfile, dirname, expanduser, abspath
from pkg_resources import require, DistributionNotFound
from platform import system
from shutil import copyfile
from socket import gethostname
from sys import argv, exit, modules, _getframe
from time import time

from floopcli.config import Config, \
        ConfigFileDoesNotExist, \
        MalformedConfigException, \
        UnmetHostDependencyException, \
        RedundantCoreConfigException
from floopcli.iot.core import build, create, destroy, ps, push, run, test, \
        CoreSourceNotFound, \
        CoreBuildException, \
        CoreCreateException, \
        CoreRunException, \
        CoreTestException, \
        CoreCommunicationException, \
        CorePSException, \
        CoreDestroyException 

logger = logging.getLogger(__name__)

_FLOOP_CONFIG_DEFAULT_FILE = './floop.json'

_FLOOP_USAGE_STRING = '''
floop [-c custom-config.json] <command> [<args>]

Supported commands:
    config      Generate a default configuration file: {}
    create      Create cores defined in configuration file
    push        Push code from host to target(s)
    build       Push and build code from host on target(s)
    run         Push, build, and run code from host on target(s)
    test        Push, build, and test code from host on target(s)
    ps          Show all running tests and runs on target(s)
    logs        Show logs with time stamps
    destroy     Destroy cores, uninstall environment from target(s)  
'''

class IncompatibleCommandLineOptions(Exception):
    '''
    Provided CLI commands and flags cannot be used together
    '''
    pass

def quiet() -> None:
    '''
    Remove console handler from logger to prevent printing to stdout

    This is a convenience function that you can use for defining
    verbose flags for CLI commands. If the flag is present, do nothing.
    If the -v flag is absent, then call quiet() inside of the method.
    '''
    log = logging.getLogger()
    # need to loop over current index of all handlers to prevent race condition
    for handler in log.handlers[:]:
        if handler.name == 'console': #type: ignore
            log.removeHandler(handler)

class FloopCLI(object):
    '''
    CLI entry point, handles all CLI calls

    Parses all CLI commands then calls the appropriate
    class method matching the CLI commands
    '''
    def __init__(self) -> None:
        parser = argparse.ArgumentParser(description='Floop CLI tool',
                usage=_FLOOP_USAGE_STRING)
        parser.add_argument('--version',
                help='Print floop CLI version',
                action='store_true')
        # handle --version flag
        if len(argv) == 2 and argv[-1] == '--version':
            args = parser.parse_args(argv[1:])
            if args.version:
                try:
                    version = require('floopcli')[0].version
                    print(version)
                    exit(0)
                # TODO: test in an environment where floop executable exists
                # but floopcli pip package is no longer installed
                except DistributionNotFound:
                    exit('''Error| pip package "floopcli" is not installed\n\n
\tOptions to fix this error:\n\
\t--------------------------\n\
\tInstall floop via pip3: pip3 install floopcli
''')
        parser.add_argument('-c', '--config-file', 
                help='Specify a non-default configuration file')
        parser.add_argument('command', help='Subcommand to run')
        config_file = _FLOOP_CONFIG_DEFAULT_FILE
        try:
            # the index of the CLI call where the commands start
            self.command_index = 2
            '''List index of where the CLI commands start'''
            if len(argv) > 3:
                if argv[1] not in ['-c', '-config-file']:
                    args = parser.parse_args(argv[1:2])
                else:
                    args = parser.parse_args(argv[1:4])
                if 'config' in argv and args.config_file:
                    raise IncompatibleCommandLineOptions('-c and config')
                if 'logs' in argv and args.config_file:
                    raise IncompatibleCommandLineOptions('-c and logs')
                if args.config_file:
                    config_file = args.config_file
                    self.command_index = 4 
            elif len(argv) > 1:
                if argv[1] in ['-c', '-config-file']:
                    args = parser.parse_args(argv[1:3])
                else:
                    args = parser.parse_args(argv[1:2])
            else:
                parser.print_help()
                exit(1)
            if not hasattr(self, args.command):
                exit('''Error| Unknown floop command: {}\n\n
\tOptions to fix this error:\n\
\t--------------------------\n\
\tTo see supported commands, run floop with no command: floop\n\
'''.format(args.command))
            if args.command not in ['config', 'logs']:
                floop_config = Config(
                        config_file=config_file).read()
                self.cores = floop_config.parse()
                '''Valid cores defined in the config file'''
            # this runs the method matching the CLI argument
            getattr(self, args.command)()
        # all CLI stdout/stderr output should come from here
        except IncompatibleCommandLineOptions:
            exit('''Error| Incompatible commands and flags: -c and config\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tUse the -c flag to point to a non-default config file: floop -c your-config-file.json'\n\
\tGenerate a default config file by running: floop config\n\
\tCopy an existing floop config file to the default path: {}\n\
\tOnly use one of the following: -c or config\n\
'''.format(_FLOOP_CONFIG_DEFAULT_FILE))
        except ConfigFileDoesNotExist:
            exit('Error| floop config file not found: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCopy an existing floop config file to the default path: {}\n\
\tGenerate a default config file by running: floop config\n\
\tUse the -c flag to point to a non-default config file: floop -c your-config-file.json'.format(
    config_file, _FLOOP_CONFIG_DEFAULT_FILE))
        # maintain this though it doesn't run just in case 
        except CoreSourceNotFound:
            exit('''Error| Cannot find host_source in config file: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tMake a new host_source and define it in config file\n\
\tChange host_source in config file to a valid filepath\n\
\tMake sure you have permission to access the files in host_source'''.format(config_file))
        except RedundantCoreConfigException as e:
            exit('''Error| Redundant address or name for cores in config: {} in {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tEdit config file so all core names and addresses are unique\n\
'''.format(str(e), config_file))
        except MalformedConfigException:
            exit('''Error| Config file is malformed: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCopy an existing valid floop config file to the default path: {}\n\
\tGenerate a default config file by running: floop config\n\
\tUse the -c flag to point to a non-default config file: floop -c your-config-file.json'\n\
'''.format(config_file, _FLOOP_CONFIG_DEFAULT_FILE))
        except UnmetHostDependencyException as e:
            exit('''Error| Unmet dependency on host: {}\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tInstall dependency for your operating system\n\
'''.format(str(e)))
        except CoreBuildException as e:
            exit('''Error| Build on target core returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck floop logs for this core: floop logs -m core-name\n\
''')
        except CoreCreateException as e:
            exit('''Error| Create target core returned non-zero error or timed out\n\n\
\tOptions to fix this error:\n\
\tCheck that your target operating system has passwordless sudo for your SSH user\n\
\tCheck that you have permission to access target_source for all cores\n\
\tCheck floop logs for this core: floop logs -m core-name\n\
''')
        except CoreDestroyException as e:
            exit('''Error| Destroy target core returned non-zero error\n\n\
\tOptions to fix this error:\n\
\tCheck that you have permission to access target_source for all cores\n\
\tCheck that you have Internet access from the host\n\
\tCheck floop logs for this core: floop logs -m core-name\n\
''')
        except CoreRunException as e:
            exit('''Error| Run on target core returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck floop logs for this core: floop logs -m core-name\n\
''')
        except CoreTestException as e:
            exit('''Error| Test on target core returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck floop logs for this core: floop logs -m core-name\n\
''')
        except CoreCommunicationException as e:
            exit('''Error| Communication with target core returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck that you have permission to access target_source for all cores\n\
\tCheck that you have Internet access from the host\n\
\tCheck that the core is still accessible at the address in your config file\n\
''')
        except CorePSException as e:
            exit('''Error| ps on target core returned non-zero error\n\n\
\tOptions to fix this error:\n\
\t--------------------------\n\
\tCheck that you have Internet access from the host\n\
\tCheck that the core is still accessible at the address in your config file\n\
\tTry to re-create the target core: floop create\n\
''')

    def __log(self, level: str, message: str) -> None:
        '''
        Wrapper for logging CLI methods that do not interact with targets

        Args:
            level (str):
                logger logging level (only use 'info' or 'error')
            message (str):
                message to log
                
        '''
        if hasattr(logger, level):
            message = '{} (host) - {}: {}'.format(
                    gethostname(), 
                    _getframe(1).f_code.co_name, # calling-function name
                    message)
            getattr(logger, level)(message)

    def config(self) -> None:
        '''
        Generate default configuration file
        '''
        parser = argparse.ArgumentParser(
                description='Configure CLI settings for all projects')
        parser.add_argument('-o', '--overwrite',
                help='Overwrite configuration file with defaults',
                action='store_true')
        args = parser.parse_args(argv[2:])
        if isfile(_FLOOP_CONFIG_DEFAULT_FILE):
            self.__log('info', 'Configuration file already exists: {}'.format(
                _FLOOP_CONFIG_DEFAULT_FILE
                )
            )
            # if the file exists and will not be overwritten, just move on
            if not args.overwrite:
                return
            backup_file = '{}.backup-{}'.format(_FLOOP_CONFIG_DEFAULT_FILE, time())
            copyfile(_FLOOP_CONFIG_DEFAULT_FILE, backup_file)
            self.__log('info', 
                    'Copied existing config file {} to backup file: {}'.format(
                _FLOOP_CONFIG_DEFAULT_FILE, backup_file))
        makedirs(dirname(_FLOOP_CONFIG_DEFAULT_FILE),
                exist_ok=True)
        with open(_FLOOP_CONFIG_DEFAULT_FILE, 'w') as c:
            # using the default_config attribute is kind of a hack
            json.dump(Config(_FLOOP_CONFIG_DEFAULT_FILE).default_config, c)
        self.__log(
                'info',
                'Wrote default configuration to file: {}'.format(
            _FLOOP_CONFIG_DEFAULT_FILE
            )
        )

    def create(self) -> None:
        '''
        Create new Docker Machines for each core in the configuration
        '''
        parser = argparse.ArgumentParser(
                description='Initialize single project communication between host and core(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        parser.add_argument('-t', '--timeout',
                help='Time to wait during creation before raising error')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        timeout = 120
        if args.timeout:
            timeout = int(args.timeout)
        with Pool() as pool:
            pool.map(partial(create, timeout=timeout), self.cores)

    def ps(self) -> None:
        '''
        Show running applications and tests on all targets
        '''
        # TODO: add metrics command to get resource usage info AND process info
        parser = argparse.ArgumentParser(
                description='List all initiated core(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        with Pool() as pool:
            pool.map(ps, self.cores)
     
    def logs(self) -> None:
        '''
        Print target logs to the host console
        '''
        # TODO: add -f option (bonus if it's pipe-able)
        parser = argparse.ArgumentParser(
                description='Logs from initialized core(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        parser.add_argument('-m', '--match',
                help='Print lines that contain the match term')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        with open('floop.log') as log:
            for line in log.readlines():
                if args.match is not None:
                    if args.match in line:
                        print(line, end="")
                elif not line == '\n':
                    print(line, end="")

    def push(self) -> None:
        '''
        Push code from host to all targets

        Automatically synchronizes code between host and targets.
        If you delete a file in the host source, then that file will
        be deleted on all targets.
        '''
        # TODO: add .floopignore ?
        parser = argparse.ArgumentParser(
                description='Push code from host to core(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        with Pool() as pool:
            pool.map(push, self.cores)

    def build(self) -> None:
        '''
        Build code on all targets, using Dockerfile in source directory

        Automatically performs a push before building in
        order to ensure that the host and targets have
        the same code.
        '''
        # TODO: add -v command to tee build outputs to logs AND local stdout
        parser = argparse.ArgumentParser(
                description='Build code on core(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        with Pool() as pool:
            pool.map(build, self.cores)

    def run(self) -> None:
        '''
        Run code on all targets, using Dockerfile in source directory

        Automatically performs a push and a build
        in order to ensure that the host and targets
        have the same code.
        '''
        # TODO: add -v command to tee build outputs to logs AND local stdout
        parser = argparse.ArgumentParser(
                description='Run code on core(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        with Pool()as pool:
            pool.map(run, self.cores)
                
    def test(self) -> None:
        '''
        Test code on all targets, using Dockerfile.test in source directory

        Automatically performs a push and a build
        in order to ensure that the host and targets
        have the same code.
        '''
        parser = argparse.ArgumentParser(
                description='Test code on core(s)')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        with Pool()as pool:
            pool.map(test, self.cores)

    def destroy(self) -> None:
        '''
        Destroy project, code, and environment on all targets

        Does not remove local source code, builds, test, or logs.
        '''
        parser = argparse.ArgumentParser(
                description='Destroy project, code, and environment on core(s) but not host')
        parser.add_argument('-v', '--verbose',
                help='Print system commands and results to stdout',
                action='store_true')
        args = parser.parse_args(argv[self.command_index:])
        if not args.verbose:
            quiet()
        with Pool() as pool:
            pool.map(destroy, self.cores)
