# VSCO Downloader 
[![Python version](https://img.shields.io/pypi/pyversions/vsco-downloader)](#)
[![Release](https://img.shields.io/github/v/release/benhacka/vsco-downloader)](#)
[![pypi](https://img.shields.io/pypi/v/vsco-downloader)](#)
[![GitHub last commit](https://img.shields.io/github/last-commit/benhacka/vsco-downloader)](#)
[![Issues](https://img.shields.io/github/issues-raw/benhacka/vsco-downloader)](#)
[![MIT License](https://img.shields.io/github/license/benhacka/vsco-downloader)](https://github.com/benhacka/vsco-downloader/blob/master/LICENSE)

## [![Rus README](https://www.countryflags.io/ru/shiny/24.png) Православная версия README](https://github.com/benhacka/vsco-downloader/blob/master/RU_README.md)
###### This is a simple console async downloader from [vsco.co](vsco.co) used original web REST requests.
So there is no fcking CLI/GUI here as befits normal scripts.  
It works through a call from the terminal 
(*Sry, win-users, I know that really can be bad for yours...*)  
Btw sup _2ch⚡_ and _VSCO находок группа_

[CHANGELOG.md](https://github.com/benhacka/vsco-downloader/blob/master/CHANGELOG.md)

## Requirements
All python requirements in the `requirements.txt`:
- `aiohttp`
- `aiofiles`  

To download videos in _m3u8_ format (parted videos with large size), you need compiled `ffmpeg`, see description for a `--ffmpeg-bin` argument


## Installation
### Easy and recommended installation with `PIP`
- Install:  
```
pip install vsco-downloader
```
- Upgrade:  
```
pip install vsco-downloader --upgrade
```
### Install from source
#### Common step
```
git clone https://github.com/benhacka/vsco-downloader
cd vsco-downloader
```
- For Windows users: change `python3` with `python` in all console command   
- You can call the script from any directory in terminal simply by typing the command `vsco-downloader` after installing the package on the system (installation via **var2** or **var3**)



#### [var 1]. Usage w/o install dist pkg (_I do not recommend this method_)
```
python3 -m pip install -r requirements.txt
```
- 1.1 Run main from package:  
`python3 -m vsco_downloader`

- 1.2 Run a script:  
`python3 vsco_downloader.py`

#### or [var 2]. Install package with setup.py
```
python3 setup.py install --user
```
- For Linux users: you can run w/o `--user` but with `sudo` for installing in `/usr/lib/python3.*/site-packages/`. 
With `--user` it will install in the `~/.local/bin/` 
_(depends on the distribution... i use arch btw [it's a stupid lie i use the best of arch - manjaro])_

- For Windows users: `--user` is not required (I think so..?)
#### or [var 3]. Install package with pip from github 
```
python3 -m pip install git+https://github.com/benhacka/vsco-downloader.git
```


## Use cases
All use cases wrote for installed package and calling with `vsco-downloader`  
I highly recommend you to set `vsco_download_path` environment variable (see _Usage help_). 

1. Download users: *foo*, *bar* and *baz*:  
`vsco-downloader foo bar baz`
  
2. Download users *foo*, *bar* and *baz* consistently:  
`vsco-downloader foo bar baz -l 1 ` 

3. Download only photos for *bar*, *baz*:  
`vsco-downloader bar baz -r mini-video video`

4. Only save download links w/o downloading content for *foo*, *bar*:  
`vsco-downloader foo bar -r all -p`

5. Download from file and args with skipping existing to ~/Download  
```sh
# show file with accs
$ cat accs_to_dl

foo


https://vsco.co/baz/gallery
```
`vsco-downloader bar -u accs_to_dl -s -d /home/username/Download/`
6. Download without restoring the names of files that are in the folder without a date as a prefix in the name
(if the file name matches the name of the direct link)
`vsco-downloader foo bar baz -nr`  

For more info see Usage help

## Usage help (*help menu*)
```plaintext
VSCO downloader

positional arguments:
  users                 urls/usernames. The script supports multiple download with passing to this argument. Urls can be either
                        to the gallery or to a separate file (the entire profile will be downloaded). Both short (from the mobile
                        version) and long urls (desktop browser) format are supported

optional arguments:
  -h, --help            show this help message and exit
  -u USERS_FILE_LIST, --users-file-list USERS_FILE_LIST
                        Same as the users but list of targets in file (one per line)
  --ffmpeg-bin FFMPEG_BIN
                        Name for ffmpeg binary that can be used for calling from terminal. Default "ffmpeg". If you have
                        installed ffmpeg from repo it should be in the /usr/bin/ffmpeg"
  --download-path-variable DOWNLOAD_PATH_VARIABLE
                        The download path in your environment variable. Default "vsco_download_path" It can be an export in the
                        shellrc (~/.bashrc for example)for Linux users. For Win users it is something like system environments.
  -d DOWNLOAD_PATH, --download-path DOWNLOAD_PATH
                        Force downloading path. If this arg passed possible path from --download-path-variable will be reloaded
                        (priority arg). By default env path is empty download path is "." (current dir).
  -r [{photo,mini-video,video} ...], --disabled-content [{photo,mini-video,video} ...]
                        Disabled of downloading some type of a content.Possible types: photo, mini-video, video
  -l min 1; max 500, --download-limit min 1; max 500
                        Limit for all get request at same time. Default 100
  -f min 1; max 100, --max-fmpeg-threads min 1; max 100
                        Limit for for ffmpeg concat threads at same time. Default 10
  -b BLACK_LIST_USER_FILE, --black-list-user-file BLACK_LIST_USER_FILE
                        File with usernames/full urls — one per line, to skip scraping and downloading
  -s, --skip-existing   Skip scrapping and downloading steps for existing users from download folder. Pass the param for
                        skipping, default - False
  -c {ts,mp4}, --container-for-m3u8 {ts,mp4}
                        A container for stream (m3u8) videos. Default "mp4", a possible alternative is "ts".
  -p, --save-parsed-download-urls
                        Store urls in the file into user dir. Filename has saving datetime so this will not overwrite old links.

  -nr, --no-restore-datetime
                        The script trying to restore file creation date before
                        downloading to skip downloading step for the files saved w/o
                        datetime. Pass the arg for skipping this step.
  -v, --version         Show the current script version

Console VSCO downloader
```
