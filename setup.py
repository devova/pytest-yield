#!/usr/bin/env python

from setuptools import setup

setup(
    name='pytest-yield',
    packages=['pytest_yield'],
    description='PyTest plugin to run tests concurrently, each `yield` switch context to other test',
    long_description=open("README.md").read(),
    author='Volodymyr Trotsyshyn',
    author_email='devova@gmail.com',
    use_2to3=True,
    url='https://github.com/devova/pytest-yield',
    py_modules=['pytest_yield'],
    install_requires=["pytest>=3.0"],
    keywords=['testing', 'pytest'],
    classifiers=[],
    setup_requires=[
        'setuptools_scm',
    ],
    use_scm_version={'root': '.', 'relative_to': __file__},
    entry_points={
        'pytest11': [
            'yield = pytest_yield.plugin',
        ]
    }
)
