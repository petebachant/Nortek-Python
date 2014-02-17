#!/usr/bin/env python
# coding=utf-8

from distutils.core import setup

setup(
    name='PdCommPy',
    version='0.0.1',
    author='Pete Bachant',
    author_email='petebachant@gmail.com',
    modules=['pdcommpy'],
    scripts=[],
    url='https://github.com/petebachant/PdCommPy.git',
    license='LICENSE',
    description='Package for working with Nortek instruments.',
    long_description=open('README.md').read()
)
