from __future__ import unicode_literals

import re

from setuptools import setup, find_packages


def get_version(filename):
    init_py = open(filename).read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", init_py))
    return metadata['version']


setup(
    name='Leapcast',
    version=get_version('leapcast/__init__.py'),
    url='http://www.mopidy.com/',
    license='MIT',
    author='Janez Troha',
    author_email='janez.troha@gmail.com',
    description='ChromeCast functionality for any device',
    long_description=open('README.md').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'tornado',
        'requests'
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
