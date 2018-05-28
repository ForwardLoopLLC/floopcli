import pytest

from os import remove
from os.path import abspath, dirname, isfile

from floopcli.config import Config, ConfigFileDoesNotExist, CannotSetImmutableAttributeException, MalformedConfigException, RedundantCoreConfigException
from floopcli.test.fixture import *

def test_floop_config_init(fixture_valid_config_file):
    Config(fixture_valid_config_file)

def test_floop_config_read(fixture_valid_config_file):
    Config(fixture_valid_config_file).read()

def test_floop_config_nonexistent_file_does_not_read():
    with pytest.raises(ConfigFileDoesNotExist):
        Config('definitely/not/a/real/config').read()

def test_floop_config_cannot_reset_config(fixture_valid_config_file):
    floop_config = Config(fixture_valid_config_file).read()
    with pytest.raises(CannotSetImmutableAttributeException):
        floop_config.config = ''

def test_floop_config_malformed_config_fails(fixture_malformed_config_file):
    with pytest.raises(MalformedConfigException):
        Config(fixture_malformed_config_file).read().parse()

def test_floop_config_incomplete_config_fails(fixture_incomplete_config_file):
    with pytest.raises(MalformedConfigException):
        Config(fixture_incomplete_config_file).read().parse()

def test_floop_config_parse(fixture_valid_config_file):
    Config(fixture_valid_config_file).read().parse()

def test_floop_config_redundant_config_fails(fixture_redundant_config_file):
    with pytest.raises(RedundantCoreConfigException):
        Config(fixture_redundant_config_file).read().parse()

def test_floop_config_missing_property_config_fails(fixture_missing_property_config_file):
    with pytest.raises(MalformedConfigException):
        Config(fixture_missing_property_config_file).read().parse()
