from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()


setup(
    author='John Clary',
    author_email='john.clary@austintexas.gov',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        # Pick your license as you wish (should match "license" above)
        'License :: Public Domain',
        'Programming Language :: Python :: 3'
    ],
    description='A Python API wrapper for interacting with Knack applications.',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
      'pytz',
      'requests'
    ],
    keywords='knack api api-client integration python',
    license='Public Domain',
    name='knackpy',
    packages=['knackpy'],
    test_suite='nose.collector',
    tests_require=['nose'],
    url='http://github.com/cityofaustin/knackpy',
    version='0.0.13',
)