#!/usr/bin/env python
# -*- coding: utf-8 -*-

from folan import __version__
from setuptools import setup
import os
import sys


if sys.argv[-1] == "publish":
    if os.path.exists('dist/'):
        if os.listdir('dist'):
            raise Exception("Clean dist/ first.")
    os.system("python setup.py sdist bdist_wheel --universal")
    os.system("twine upload dist/*")
    sys.exit()

setup(
    name='folan',
    version=__version__,
    author='Matthew Timms',
    author_email='matthewtimms@live.com.au',
    description='Sharing files over LAN',
    license='MIT',
    url='https://github.com/MattTimms/folan',
    py_modules=['folan'],
    install_requires=[
        'docopt',
        'psutil',
        'pytest'
    ],
    classifiers=[  # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Topic :: Communications :: File Sharing',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    entry_points={
        'console_scripts': [
            'folan = folan:_entry_point'
        ]
    },
    keywords=['file sharing', 'tcp', 'lan'],
)
