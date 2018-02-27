#!/usr/bin/env python

from setuptools import setup

setup(
    name='pytest-yield',
    version='0.1',
    description='PyTest plugin to run tests concurrently, each `yield` switch context to other test',
    long_description=open("README.md").read(),
    author='Volodymyr Trotsyshyn',
    author_email='devova@gmail.com',
    url='https://github.com/devova/pytest-yield',
    py_modules=['pytest_yield'],
    install_requires=["pytest>=3.0"],
    classifiers=[
        'Development Status :: 4 - Testing/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GPL License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing'
    ],
    entry_points={
        'pytest11': [
            'pytest_yield = pytest_yield',
        ]
    }
)
