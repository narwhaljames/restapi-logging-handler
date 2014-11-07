import os
from setuptools import setup


def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(
    name='restapi-logging-handler',
    version='0.1',
    description='A handler for the python logging module that allows \
        sending logs through a REST-ful API. With Loggly support.',
    long_description=(read('README.md')),
    packages=['restapi_logging_handler'],
    install_requires=['requests'],
    author='RJ Gilligan',
    author_email='rj.gilligan@nrgnergy.com',
    url='https://github.com/narwhaljames/restapi-logging-handler.git',
    download_url='https://github.com/narwhaljames/restapi-logging-handler/tarball/0.1',
    keywords=['rest', 'api', 'logging', 'handler', 'loggly'],
    classifiers=[],
    license='MIT',
    test_suite='nose.collector',
    tests_require=['nose'],
)
