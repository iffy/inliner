#!/usr/bin/env python
# Copyright (c) Matt Haggard
# See LICENSE for details.


from distutils.core import setup

setup(
    name='inliner',
    version='0.2.1',
    description='Inlines external HTML resources',
    author='Matt Haggard',
    author_email='haggardii@gmail.com',
    url='https://github.com/iffy/inliner',
    packages=[],
    install_requires=[
        'lxml',
        'requests',
        'BeautifulSoup',
    ],
    scripts=[
        'inliner.py',
    ]
)