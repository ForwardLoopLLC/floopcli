import json
from copy import copy
from time import time
from os import rename
from os.path import isdir, isfile
from shutil import which
from floopcli.iot.core import Core 
from typing import Any, Dict, List, TypeVar

# default config to write when using floop config 
_FLOOP_CONFIG_DEFAULT_CONFIGURATION = {
    'groups' : {
        'default': { 
            'host_rsync_bin' : which('rsync'),
            'host_docker_machine_bin' : which('docker-machine'),
        },
        'group0' :{
            'cores' : {
                'default': {
                    'host_source' : './'
                },
                'core0' : {
                    'target_source' : '/home/floop/floop/',
                    'address' : '192.168.1.100', 
                    'port' : '22',
                    'user' : 'floop',             
                    'host_key' : '~/.ssh/id_rsa', 
                }
            }
        }
    },
}

def _flatten(config : dict) -> List[dict]:
    '''
    Flatten floop configuration

    Args:
        config (dict):
            config dictionary 

    Raises:
        :py:class:`floopcli.config.MalformedConfigException`:
            config has no default group, default core, and/or core address
    '''
    flat_config = []
    try:
        default = config['groups']['default']
        for group, gval in config['groups'].items():
            if group != 'default':
                group_default = gval['cores']['default']
                for core, dval in gval['cores'].items():
                    if core != 'default':
                        core_config = copy(default)
                        for key, val in group_default.items():
                            core_config[key] = val
                        for key, val in dval.items():
                            core_config[key] = val
                        core_config['group'] = group
                        core_config['core'] = core
                        assert(core_config['address'])
                        flat_config.append(core_config)
        return flat_config
    # forces config to have default groups and cores
    except (TypeError, KeyError, AssertionError) as e:
        raise MalformedConfigException(str(e))

class CannotSetImmutableAttributeException(Exception):
    '''
    Tried to set immutable attribute after initialization
    '''
    pass

class MalformedConfigException(Exception):
    '''
    Provided config did not have all expected keys
    '''
    pass

class MalformedCoreConfigException(Exception):
    '''
    At least one core in provided config did not have all expected keys
    '''
    pass

class ConfigFileDoesNotExist(Exception):
    '''
    Provided configuration file does not exist
    '''
    pass 

class TargetBuildFileDoesNotExist(Exception):
    '''
    Provided "host_source_directory" in config has no Dockerfile
    '''
    pass 

class UnmetHostDependencyException(Exception):
    '''
    Provided dependency binary path does not exist
    '''
    pass

class RedundantCoreConfigException(Exception):
    '''
    At least one core in the config has a redundant name or address 
    '''
    pass

def _read_json(json_file : str) -> dict:
    '''
    Convenient wrapper for reading .json file into dict

    Args:
        json_file (str):
            Path to json file
    Returns:
        dict:
            dictionary of json file content
    '''
    try:
        with open(json_file) as j:
            return json.load(j)
    except json.decoder.JSONDecodeError:
        raise MalformedConfigException('Invalid JSON')

ConfigType = TypeVar('ConfigType', bound='Config')
'''Generic self config type for stateful method return'''

class Config(object):
    def __init__(self, config_file : str) -> None:
        self.default_config = _FLOOP_CONFIG_DEFAULT_CONFIGURATION 
        self.config_file = config_file

    @property
    def config(self) -> List[Dict[str, Any]]:
        '''
        Flattened configuration read from file
        '''
        return self.__config

    @config.setter
    def config(self, value : List[Dict[str, Any]]) -> None:
        if hasattr(self, 'config'):
            raise CannotSetImmutableAttributeException('config')
        self.__config = value

    def read(self: ConfigType) -> ConfigType:
        '''
        Read configuration file

        Raises:
            :py:class:`ConfigFileDoesNotExist`:
                configuration file does not exist

        Returns:
            :py:class:`floopcli.config.Config`:
                configuration object with config attribute
        '''
        config_file = self.config_file
        if not isfile(config_file) or config_file is None:
            raise ConfigFileDoesNotExist(config_file)
        raw_config = _read_json(config_file)
        # throws malformed errors
        config = _flatten(raw_config)
        addresses = [] #type: List[str]
        for core in config:
            if core['address'] in addresses:
                raise RedundantCoreConfigException(core['address'])
            addresses.append(core['address'])
        self.config = config
        return self

    def parse(self) -> List[Core]:
        '''
        Parse configuration into list of cores

        Raises:
            :py:class:`floopcli.config.UnmetHostDependencyException`:
                rsync and/or docker-machine binary path does not exist
            :py:class:`floopcli.config.MalformedConfigException`:
                configuration is missing keys expected by :py:class:`floopcli.iot.core.Core`

        Returns:
            [:py:class:`floopcli.iot.core.Core`]:
                list of cores defined in config
        '''
        # only handle dependency checking
        # let core handle host and target checking to prevent race
        for core in self.config:
            for key, val in core.items():
                if key.endswith('_bin'):
                    if not isfile(val) or val is None:
                        err = 'Dependency {} not found at {}'.format(
                                key.replace('_bin', ''), val)
                        # TODO: test in an environment with unmet dependencies
                        raise UnmetHostDependencyException(err)
        cores = []
        for core in self.config:
            try:
                cores.append(Core(**core))
            except TypeError as e:
                missing_key = str(e).split(' ')[-1]
                err = '{} (core) has no {} (property)'.format(
                        core['core'], missing_key)
                raise MalformedConfigException(err)
        return cores
