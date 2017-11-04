from setuptools import setup

setup(
    author='John Clary',
    author_email='john.clary@austintexas.gov',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        # Pick your license as you wish (should match "license" above)
        'License :: Public Domain',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
    ],
    description='Python API wrapper for interacting with Knack applications.',
    install_requires=[
      'arrow',
      'requests'
    ],
    keywords='knack api api-client integration',
    license='Public Domain',
    name='knackpy',
    packages=['knackpy'],
    test_suite='nose.collector',
    tests_require=['nose'],
    url='http://github.com/cityofaustin/knack-py',
    version='0.0.4',
)
