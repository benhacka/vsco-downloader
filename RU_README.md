# VSCO Downloader
[![Python version](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue)]()
[![Release](https://img.shields.io/github/v/release/benhacka/vsco-downloader)]()
[![GitHub last commit](https://img.shields.io/github/last-commit/benhacka/vsco-downloader)]()
[![Issues](https://img.shields.io/github/issues-raw/benhacka/vsco-downloader)]()
[![MIT License](https://img.shields.io/github/license/benhacka/vsco-downloader)](https://github.com/benhacka/vsco-downloader/blob/master/LICENSE)

## [![Original README](https://www.countryflags.io/us/shiny/24.png) Original README](https://github.com/benhacka/vsco-downloader)
###### Простенький асинхронный консольный скриптик для скачки с [vsco.co](vsco.co).
Скрипт без всяких залупных консольных и гуевых интерфейсов, как и пологается ему быть, если это не скрипт курильщика  
Работает через вызов из терминала  
(Соря виндовозы, я знаю, что это может быть плохой новостью)  
Кста, сап _Харкач⚡_ и _VSCO находок группа_

[CHANGELOG.md - изменения по релизам](https://github.com/benhacka/vsco-downloader/blob/master/CHANGELOG.md)

## Зависимости
Все питонячьи зависимости в файле `requirements.txt`:
- `aiohttp`
- `aiofiles`  

Для скачки видосов _m3u8_ - раздробленные на части куски видео, нужен `ffmpeg`, смотри описание для аргумента запуска `--ffmpeg-bin`


## Установка
#### Общий этап
Склонить реп и зайти в директорию:
```
git clone https://github.com/benhacka/vsco-downloader
cd vsco-downloader
```
- Для виндовозов: во всех консольных комндах ниже мб нужно поменять `python3` на `python` 
- После установки пакета в систему (установка через **вариант 2** или **вариант 3**) можно вызвать скрипт из консоли в любой директории просто набрав команду `vsco-downloader`
#### [вариант 1]. Использование без установки пакета (_Не рекомендую такой метод_)
```
python3 -m pip install -r requirements.txt
```
- 1.1 Запустить скрипт через пакет:  
`python3 -m vsco_downloader`

- 1.2 Запустить скрипт через вырожденный скрипт с вызовом главного в пакете:  
`python3 vsco_downloader.py`

#### или [вариант 2]. Установка пакета через setup.py
```
python3 setup.py install --user
```
- Для линуксоидов: можно запустить установку без `--user` но с `sudo` для установки в  `/usr/lib/python3.*/site-packages/`. C `--user` он будет установлен в `~/.local/bin/`, но это может отличать от дистра к дистру (а мб и нет, не ебу, в этом зоопарке всякое можеты быть).
- Для виндовозов: `--user` не требуется (сокрее всего так, но хз что будет если с ним все же попытаться поставить)
#### or [var 3]. Установка через pip с гита 
```
python3 -m pip install git+https://github.com/benhacka/vsco-downloader.git
```

## Примеры использования
Все примеры написаны для установленного в систему пакета с вызовом через `vsco-downloader`  
Крайне рекомендую установить переменную окружения `vsco_download_path` (см. _Помощь в использовании_). 

1. Скачать пользователей: *foo*, *bar* and *baz*:  
`vsco-downloader foo bar baz`
  
2. Скачать пользователей *foo*, *bar* and *baz* последовательно (по одному):  
`vsco-downloader foo bar baz -l 1 ` 

3. Скачать только фото пользователей *bar*, *baz*:  
`vsco-downloader bar baz -r mini-video video`

4. Сохранить только ссылки на контент без скачки для пользователей *foo*, *bar*:  
`vsco-downloader foo bar -r all -p`

5. Скачать из файла и аргументом, пропустив существующие акки в ~/Download  
```sh
# просмотр файл с акками
$ cat accs_to_dl

foo

https://vsco.co/baz/gallery
```
`vsco-downloader bar -u accs_to_dl -s -d /home/username/Download/`
6. Скачка без восстановления имен файлов, которые лежат в папке без даты в виде префикса в имени 
(если имя файла соответствует имени по прямой ссылке)
`vsco-downloader foo bar baz -nr`  

Больше инфы в _помощь в использовании_ 

## Помощь в использовании (*меню help в скрипте*)

```plaintext
VSCO downloader

позиционные аргументы:
  users                 ссылка/юзернеймы. Скрипт поддерживает загрузку с нескольких источников через этот аргуемент. 
                        Ссылка может быть как на галерею, так и на отдельный файл (скачивается весь конент профиля). 
                        Поддерживаются короткие (то, что шарится с мобилок) и длинные форматы ссылок 
                        (ссылка в адресной строке десктопного браузера)

именные аргументы:
  -h, --help            show this help message and exit
  -u USERS_FILE_LIST, --users-file-list USERS_FILE_LIST
                        То же самое что и users, но из файла (по одной ссылке или юзернейму на строке)
  --ffmpeg-bin FFMPEG_BIN
                        Имя ffmpeg, через которое скрипт сможет денуть его. По умолчанию "ffmpeg". 
                        Если ffmpeg был установлен с репа, то скорее всего лежит в /usr/bin/ffmpeg 
                        и доступен через команду ffmpeg в любом месте"
  --download-path-variable DOWNLOAD_PATH_VARIABLE
                        Переменная окружения пути скачки. По умолчанию "vsco_download_path" Может быть задана через экспорт 
                        в shellrc (~/.bashrc for example) для линуксоидов. Для виндовозов устанавливается 
                        где-то в system environments.
  -d DOWNLOAD_PATH, --download-path DOWNLOAD_PATH
                        Форсированный путь для скачки. Если аргумент задан, то перегружает vsco_download_path
                        (более приоритетная). Без vsco_download_path не задан, то этот аргумент "." 
                        (текущая папка откуда вызван скрипт).
  -r [{photo,mini-video,video} ...], --disabled-content [{photo,mini-video,video} ...]
                        Отключает загрузку выбранного типа контента. Возможные типы: photo, mini-video, video
  -l min 1; max 500, --download-limit мин 1; макс 500
                        Лимит на запросы к серверам в один момент. Default 100
  -f min 1; max 100, --max-fmpeg-threads мин 1; макс 100
                        Лимит на склейку с ffmpeg в один момент. Default 10
  -b BLACK_LIST_USER_FILE, --black-list-user-file BLACK_LIST_USER_FILE
                        Файл с именами или полными ссылками (короткие игнорируются), для пропуска этапов сбора и скачки
  -s, --skip-existing   Пропустить этапы сбора и скачки для пользователей папки с именами которых уже сущесвуют. 
                        Для включения опции указать аргумент, по умолчанию выключено
  -c {ts,mp4}, --container-for-m3u8 {ts,mp4}
                        Контейнер для стриминговых (m3u8) видео. По умолчанию "mp4", возможная альтернатива - "ts".
  -p, --save-parsed-download-urls
                        Сохранить ссылки на контент в файл с пользователем. 
                        В имени файла текущая дата сохранения, поэтому не происходит перезапись файла.
 
  -nr, --no-restore-datetime
                        [НЕ - аргумент отрицание] Скрипт попытается восстановить дату загрузки файла перед загрузкой
                        для пропуска загрузки существующих уже файлов в именах которых нет даты. Для отключения 
                        опции надо указать этот аргумент  

Console VSCO downloader
```

