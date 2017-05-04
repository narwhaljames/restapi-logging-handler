from setuptools import setup


try:
    import pypandoc

    description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    description = open('README.md').read()

setup(
    name='restapi-logging-handler',
    version='0.2.4',
    description='A handler for the python logging module that sends logs \
        through any REST-ful API. With threading and Loggly support that \
        handles batch POSTS.',
    long_description=description,
    packages=['restapi_logging_handler'],
    install_requires=['requests-futures'],
    author='RJ Gilligan, Ethan McCreadie, Mikey Reppy',
    author_email='r.j.gilligan@nrg.com, '
                 'ethan.mccreadie@nrg.com, '
                 'mike.reppy@nrg.com',
    url='https://github.com/EnergyPlus/restapi-logging-handler.git',
    download_url=(
        'https://github.com/EnergyPlus/restapi-logging-handler.git/'
        'tarball/0.2.4'
    ),
    keywords=['rest', 'api', 'logging', 'handler', 'loggly'],
    classifiers=[],
    license='MIT',
    test_suite='nose.collector',
    tests_require=['nose'],
)
