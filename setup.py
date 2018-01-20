#!/usr/bin/env python
# -*- coding: utf-8 -*-

from folan import __version__
from setuptools import setup
import os
import sys


if sys.argv[-1] == "publish":
    if os.listdir('dist'):
        raise Exception("Clean dist/ first.")
    os.system("python setup.py sdist bdist_wheel --universal")
    os.system("twine upload dist/*")
    sys.exit()

REQUIRED = [
    'docopt==0.6.2'
]

setup(
    name='folan',
    version=__version__,
    author='Matthew Timms',
    author_email='matthewtimms@live.com.au',
    description='Sharing files over LAN',
    license=open('LICENSE', 'r').read(),
    url='https://github.com/MattTimms/folan',
    py_modules=['folan'],
    install_requires=REQUIRED,
    classifiers=[  # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Communications :: File Sharing',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': [
            'folan = folan:main'
        ]
    },
    keywords=['file sharing', 'tcp', 'lan'],
    long_description=open('README.rst').read()
)
