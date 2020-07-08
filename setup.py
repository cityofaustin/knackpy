from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    author="John Clary",
    author_email="john.clary@austintexas.gov",
    classifiers=[
        "Development Status :: 2 - Beta",
        "Intended Audience :: Developers",
        "License :: Public Domain",
        "Programming Language :: Python :: 3",
    ],
    description="A Python API client for interacting with Knack applications.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=["pytz", "requests"],
    keywords="knack api api-client integration python",
    license="Public Domain",
    name="knackpy",
    packages=["knackpy"],
    tests_require=["pytest"],
    url="http://github.com/cityofaustin/knackpy",
    version="1.0.0",
)
