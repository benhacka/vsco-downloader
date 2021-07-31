# VSCO Downloader
###### This is a simple console async downloader from [vsco.co](vsco.co).
So there is no fcking CLI/GUI here as befits normal scripts.  
It works through a call from the terminal 
(*Sry, win-users, I know that really can be bad for yours...*)  
Btw sup _2ch_ & _VSCO находок группа_

### Installation
##### Common step
```
git clone https://github.com/benhacka/vsco-downloader
cd vsco-downloader
```
##### [var 1]. Usage w/o install dist pkg
```
python3 -m pip install -r requirements.txt
python3 -m vsco_downloader
```
##### [var 2]. Install package with setup.py
```
python3 setup.py install --user
```
##### [var 3]. Install package with pip
```
python3 -m pip install git+https://github.com/benhacka/vsco-downloader.git
```

### Use cases
All use cases wrote for installed package and calling with `vsco-downloader`  
I highly recommend you to set `vsco_download_path` environment variable (see _Usage help_). 

1. Download users: *foo*, *bar* and *baz*:  
`vsco-downloader foo bar baz`
  
2. Download users *foo*, *bar* and *baz* consistently:  
`vsco-downloader foo bar baz -l 1 ` 

3. Download only photos for *bar*, *baz*:  
`vsco-downloader bar baz -r mini-video video`

4. Only save download links w/o downloading content for *foo*, *bar*:  
`vsco-downloader foo bar -r mini-video video photo -p`

5. Download from file and args with skipping existing to ~/Download  
```sh
$ cat accs_to_dl

foo


https://vsco.co/baz/gallery
```
`vsco-downloader bar -u accs_to_dl -s -d ~/Download`

For more info see Usage help

### Usage help (*help menu*)
```sh
VSCO downloader

positional arguments:
  users                 urls/usernames. The script supports multiple download with passing to this argument. Urls can be either
                        to the gallery or to a separate file (the entire profile will be downloaded). Both short (from the mobile
                        version) and long urls (desktop browser) format are supported

optional arguments:
  -h, --help            show this help message and exit
  -u USERS_FILE_LIST, --users-file-list USERS_FILE_LIST
                        Same as the users but list of targets in file (one per line
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

Console VSCO downloader
```