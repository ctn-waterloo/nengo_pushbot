#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    try:
        from ez_setup import use_setuptools
        use_setuptools()
        from setuptools import setup
    except Exception, e:
        print "Forget setuptools, trying distutils..."
        from distutils.core import setup


description = ("Nengo hooks for controlling Jorg Conradt's pushbots")
setup(
    name="nengo_pushbot",
    version="0.0.1.dev",
    author="CNRGlab at UWaterloo and APT at University of Manchester",
    author_email="https://github.com/ctn-waterloo/nengo_pushbot/issues",
    packages=['nengo_pushbot'],
    package_data={'nengo_pushbot': ['binaries/*.aplx']},
    scripts=[],
    license="GPLv3",
    description=description,
    long_description="",
    requires=[
        "nengo",
    ],
    test_suite='nengo_pushbot.test',
)
