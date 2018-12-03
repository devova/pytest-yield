#!/usr/bin/env python

from setuptools import setup

setup(
    name='pytest-yield',
    version='0.1.9',
    packages=['pytest_yield'],
    description='PyTest plugin to run tests concurrently, each `yield` switch context to other test',
    long_description=open("README.md").read(),
    author='Volodymyr Trotsyshyn',
    author_email='devova@gmail.com',
    use_2to3=True,
    url='https://github.com/devova/pytest-yield',
    download_url='https://github.com/devova/pytest-yield/archive/0.1.9.tar.gz',
    py_modules=['pytest_yield'],
    install_requires=["pytest>=3.0"],
    keywords=['testing', 'pytest'],
    classifiers=[],
    entry_points={
        'pytest11': [
            'yield = pytest_yield.plugin',
        ]
    }
)
