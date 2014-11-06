from distutils.core import setup

setup(
    version='0.1',
    description='A handler for the python logging module that allows \
        sending logs through a REST-ful API.',
    name='restapi-logging-handler',
    packages=['restapi_logging_handler'],
    install_requires=['requests'],
    author='RJ Gilligan',
    author_email='rj.gilligan@nrgnergy.com',
    url='https://github.com/energyplus/restapi-logging-handler.git',
    download_url='https://github.com/energyplus/restapi-logging-handler/tarball/0.1',
    keywords=['rest', 'api', 'logging', 'handler', 'loggly'],
    classifiers=[],
    license='MIT',
    test_suite='nose.collector',
    tests_require=['nose'],
)
