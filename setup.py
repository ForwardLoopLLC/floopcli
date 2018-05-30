from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

install_requires = [
            'argparse>=1.4.0',
            'pyyaml>=3.12',
            ]

tests_require = [
            'mypy>=0.0.590',
            'pytest>=3.5.1',
            'pytest-cov>=2.5.1',
            'sphinx>=1.7.4',
            'sphinx-tabs>=1.1.7'
            ]

extras = {
    'test': tests_require,
}

setup(
    name='floopcli',
    version='0.0.1a1',
    description='sensor development and testing tools',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    url='https://github.com/ForwardLoopLLC/floopcli',
    author='Forward Loop LLC',
    author_email='nick@forward-loop.com', 
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 3',
    ],
    keywords='sensor development devops',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    install_requires=install_requires,
    tests_require=tests_require,
    extras_require=extras,
    entry_points={
        'console_scripts': [
            'floop=floopcli.__main__:main'
        ],
    },
    project_urls={
        'Bug Reports': 'https://github.com/ForwardLoopLLC/floopcli/issues',
        'Source': 'https://github.com/ForwardLoopLLC/floopcli/issues',
    },
)
