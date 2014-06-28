#!/usr/bin/env python
# -*- coding: utf-8 -*-
b'This library requires pypy or Python 2.6, 2.7, 3.3, pypy or newer'
import io
import os
import re
from setuptools import setup, find_packages


def get_path(*args):
    return os.path.join(os.path.dirname(__file__), *args)


def read_from(filepath):
    with io.open(filepath, 'rt', encoding='utf8') as f:
        return f.read()


def get_requirements(filename='requirements.txt'):
    data = read_from(get_path(filename))
    lines = map(lambda s: s.strip(), data.splitlines())
    return [l for l in lines if l and not l.startswith('#')]

data = read_from(get_path('leapcast', '__init__.py'))
version = re.search(u"__version__\s*=\s*u?'([^']+)'", data).group(1).strip()
readme = read_from(get_path('README.rst'))

setup(
    name='Leapcast',
    version=version,
    license='MIT',
    author='Janez Troha',
    author_email='janez.troha@gmail.com',
    description='ChromeCast functionality for any device',
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    long_description=readme,
    install_requires=get_requirements(),
    test_suite='nose.collector',
    tests_require=[
        'nose',
        'flake8',
    ],
    entry_points={
        'console_scripts': [
            'leapcast = leapcast.__main__:main'
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python :: 2.7',
        'Topic :: Multimedia',
    ],
)
