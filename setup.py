#!/usr/bin/env python3
import sys
import setuptools
from vsco_downloader import __version__

if sys.version_info < (3, 7):
    sys.exit('Python < 3.7 is not supported')

with open('requirements.txt') as f:
    required = [requirement.strip() for requirement in f.readlines()]

setuptools.setup(
    name='vsco_downloader',
    version=__version__,
    description='VSCO Downloader',
    zip_safe=False,
    include_package_data=True,
    packages=setuptools.find_packages(),
    install_requires=required,
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'vsco-downloader=vsco_downloader.__main__:main',
        ]
    },
)
