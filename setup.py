# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages

from plainmenu import __version__

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VERSION_STRING = '.'.join(str(s) for s in __version__)

setup(
    name='django-plainmenu',
    version=VERSION_STRING,
    url='https://bitbucket.org/impala/django-plainmenu',
    license='GPLv3+',
    description='Very basic menu system for django apps.',
    keywords=['django', 'library', 'configuration'],
    author='Kirill Stepanov',
    author_email='mail@kirillstepanov.me',
    packages=find_packages(),
    download_url='https://bitbucket.org/impala/django-plainmenu/get/%s.tar.gz' % VERSION_STRING,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Framework :: Django',
        'Framework :: Django :: 1.8',
        'Framework :: Django :: 1.9',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    install_requires=[
        'django-treebeard<=4.3',
        'FeinCMS<1.14',
        'swapper<1.1'
    ],
    include_package_data=True,
    zip_safe=False,
)
