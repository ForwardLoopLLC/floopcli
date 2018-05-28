import logging
from os import getcwd
from os.path import isfile, dirname, realpath
from floopcli.cli import FloopCLI

logger = logging.getLogger(__name__)

def main() -> None:
    import logging.config
    import yaml

    path = dirname(realpath(__file__)) +  '/log.yaml'
    if isfile(path):
        with open(path, 'rt') as f:
            config = yaml.load(f.read())
        config['handlers']['floop']['name'] = \
            getcwd() + '/' + config['handlers']['floop']['name'] 
        logging.config.dictConfig(config)
    FloopCLI()
