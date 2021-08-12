#!/usr/bin/env python3
import setuptools
from vsco_downloader import __version__
#from vsco_downloader.__main__ import py_version_checker

#py_version_checker()

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
    include_package_data=True,
    install_requires =[
        "aiohttp~=3.7.4",
        "aiofiles~=0.7.0",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    packages=setuptools.find_packages(),
    keywords="vsco download scrape parse photo social-network".split(),
    python_requires='>=3.7',
    entry_points={
        'console_scripts': [
            'vsco-downloader=vsco_downloader.__main__:main',
        ]
    },
)
