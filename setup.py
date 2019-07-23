#!/usr/bin/python3

from setuptools import setup
from fifocator import __version__

setup(
    name = 'fifocator',
    packages = [ 'fifocator' ],
    version = __version__,
    description = 'Named pipes made easy',
    license = 'MIT',
    author = 'Avner Herskovits',
    author_email = 'avnr_ at outlook.com',
    url = 'https://github.com/avnr/fifocator',
    download_url = 'https://github.com/avnr/fifocator/tarball/' + __version__,
    install_requires=[],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Linux',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries',
    ],
)
