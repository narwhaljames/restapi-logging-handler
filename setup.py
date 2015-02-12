from setuptools import setup


try:
    import pypandoc
    description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError):
    description = open('README.md').read()

setup(
    name='restapi-logging-handler',
    version='0.2.2',
    description='A handler for the python logging module that sends logs \
        through any REST-ful API. With threading and Loggly support that \
        handles batch POSTS.',
    long_description=description,
    packages=['restapi_logging_handler'],
    install_requires=['requests-futures'],
    author='RJ Gilligan, Ethan McCreadie',
    author_email='r.j.gilligan@nrg.com, ethan.mccreadie@nrg.com',
    url='https://github.com/narwhaljames/restapi-logging-handler.git',
    download_url='https://github.com/narwhaljames/restapi-logging-handler/tarball/0.2.2',
    keywords=['rest', 'api', 'logging', 'handler', 'loggly'],
    classifiers=[],
    license='MIT',
    test_suite='nose.collector',
    tests_require=['nose'],
)
