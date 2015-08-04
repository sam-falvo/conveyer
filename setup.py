"""
Setup file for conveyer
"""
from setuptools import setup, find_packages


_NAME = "conveyer"
_VERSION = "0.1.0"


def setup_options(name, version):
    """
    :returns: a dictionary of setup options.
    """
    return dict(
        install_requires=[
            "klein",
        ],
        package_dir={"conveyer": "conveyer"},
        packages=find_packages(exclude=[]),
    )

setup(
    name=_NAME,
    version=_VERSION,
    description="A log conveyance tool from Logstash to Rackspace Cloud Agent",
    license="Apache License, Version 2.0",
    include_package_data=True,
    **setup_options(_NAME, _VERSION)
)
