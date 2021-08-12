#!/usr/bin/env python3
import setuptools
from vsco_downloader import __version__
from vsco_downloader.__main__ import py_version_checker

py_version_checker()

with open('requirements.txt') as f:
    required = [requirement.strip() for requirement in f.readlines()]

GIT_URL = 'https://github.com/benhacka/vsco-downloader'

setuptools.setup(
    name='vsco-downloader',
    version=__version__,
    description='VSCO download manager on pure REST',
    long_description_content_type='text/markdown',
    zip_safe=False,
    author='anon',
    author_email='anon@fake-mail.foobar',
    url=GIT_URL,
    download_url=f'{GIT_URL}/archive/refs/tags/v.{__version__}.tar.gz',
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=setuptools.find_packages(),
    install_requires=required,
    keywords="vsco download scrape parse photo social-network".split(),
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'vsco-downloader=vsco_downloader.__main__:main',
        ]
    },
)
