import os
from setuptools import setup


try:
    import pypandoc
    description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    description = open('README.md').read()

setup(
    name='restapi-logging-handler',
    version='0.1.9',
    description='A handler for the python logging module that sends logs \
        through any REST-ful API. Fully asyncronous. With Loggly support.',
    long_description=description,
    packages=['restapi_logging_handler'],
    install_requires=['requests-futures'],
    author='RJ Gilligan',
    author_email='rj.gilligan@nrgnergy.com',
    url='https://github.com/narwhaljames/restapi-logging-handler.git',
    download_url='https://github.com/narwhaljames/restapi-logging-handler/tarball/0.1.9',
    keywords=['rest', 'api', 'logging', 'handler', 'loggly'],
    classifiers=[],
    license='MIT',
    test_suite='nose.collector',
    tests_require=['nose'],
)
