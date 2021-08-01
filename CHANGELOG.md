# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).
  
## [0.1.1] - 2021-08-01
   
### Added
- Added pseudo-type `all` to content types to block downloading (`-r`/`--disabled-content`)
- Added `CHANGELOG.md`
- Added a simple script for running `vsco_downloader.__main__.main`
 
### Changed
- Changed all relative paths from _dot_(.) to __package name dot__ (vsco_downloader.*).

### Fixed
- Fixed `python_requires` (required 3.7+ python version but not a 3.8+ one) in the _setup.py_
- Fixed false-positive full-url checking raise

 
## [0.1.0] - 2021-07-31
 
### Added
- Whole project   