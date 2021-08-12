import argparse
import logging
import os
import sys

from vsco_downloader.container import REGISTERED_CONTENT, VscoVideo
from vsco_downloader import __version__

content_types = [
    content.verbose_content_type for content in REGISTERED_CONTENT
] + ['all']

MAX_THREAD = 500
MAX_FFMPEG_THREAD = 100
DOWNLOAD_PATH = 'vsco_download_path'


class CheckRange(argparse.Action):
    def get_check_range(self) -> range:
        raise NotImplementedError

    def __call__(self, parser, args, values, option_string=None):
        check_range = self.get_check_range()
        if values not in check_range:
            raise argparse.ArgumentError(
                self, f'The value should be in '
                f'{check_range.start, check_range.stop - 1}]')
        setattr(args, self.dest, values)


class MaxThread(CheckRange):
    def get_check_range(self) -> range:
        return range(1, MAX_THREAD + 1)


class MaxFFmpegThread(CheckRange):
    def get_check_range(self) -> range:
        return range(1, MAX_FFMPEG_THREAD + 1)


class FileSystemCheck(argparse.Action):
    @property
    def is_file(self):
        raise NotImplementedError

    def __call__(self, parser, args, values, option_string=None):
        if self.is_file:
            if not os.path.isfile(values):
                raise argparse.ArgumentError(self, f'File {values} not exists')
            setattr(args, self.dest, values)
            return
        try:
            if values:
                os.makedirs(os.path.dirname(values), exist_ok=True)
        except OSError as e:
            raise argparse.ArgumentError(self,
                                         f"Can not create a directory: {e}")
        setattr(args, self.dest, values)


class ListFile(FileSystemCheck):
    @property
    def is_file(self):
        return True


class DownloadDir(FileSystemCheck):
    @property
    def is_file(self):
        return False


def get_users_from_file(file_name):
    if not file_name or not os.path.isfile(file_name):
        return []
    with open(file_name) as user_file:
        return [user.strip().strip(';').strip(',') for user in user_file]


async def parse_arg():
    parser = argparse.ArgumentParser(description='VSCO downloader',
                                     epilog='Console VSCO downloader')
    parser.add_argument(
        'users',
        nargs='*',
        help="urls/usernames. "
        "The script supports multiple download "
        "with passing to this argument. "
        "Urls can be either to the gallery or to a separate file "
        "(the entire profile will be downloaded). "
        "Both short (from the mobile version) and long urls (desktop browser)"
        " format are supported")
    parser.add_argument('-u',
                        '--users-file-list',
                        action=ListFile,
                        help='Same as the users but list of targets in file '
                        '(one per line')
    parser.add_argument('--ffmpeg-bin',
                        default='ffmpeg',
                        help='Name for ffmpeg binary that '
                        'can be used for calling from terminal. '
                        'Default "ffmpeg". '
                        'If you have installed ffmpeg from repo '
                        'it should be in the /usr/bin/ffmpeg"')
    parser.add_argument(
        '--download-path-variable',
        help='The download path in your environment variable. '
        f'Default "{DOWNLOAD_PATH}"'
        'It can be an export in the shellrc (~/.bashrc for example)'
        'for Linux users. For Win users it is something '
        'like system environments.',
        default=DOWNLOAD_PATH)
    parser.add_argument(
        '-d',
        '--download-path',
        action=DownloadDir,
        help='Force downloading path. '
        'If this arg passed possible path from --download-path-variable '
        'will be reloaded (priority arg). '
        'By default env path is empty download path is "." (current dir).')
    parser.add_argument('-r',
                        '--disabled-content',
                        nargs='*',
                        choices=content_types,
                        help='Disabled of downloading some type of a content.'
                        f'Possible types: {", ".join(content_types)}')
    parser.add_argument(
        '-l',
        '--download-limit',
        type=int,
        default=100,
        action=MaxThread,
        metavar='min 1; max 500',
        help='Limit for all get request at same time. Default 100')
    parser.add_argument('-f',
                        '--max-fmpeg-threads',
                        type=int,
                        default=10,
                        action=MaxFFmpegThread,
                        metavar='min 1; max 100',
                        help='Limit for for ffmpeg concat threads '
                        'at same time. Default 10')
    parser.add_argument('-b',
                        '--black-list-user-file',
                        action=ListFile,
                        help='File with usernames/full urls — one per line, '
                        'to skip scraping and downloading')
    parser.add_argument('-s',
                        '--skip-existing',
                        action='store_true',
                        default=False,
                        help='Skip scrapping and downloading steps '
                        'for existing users from download folder. '
                        'Pass the param for skipping, '
                        'default - False')
    parser.add_argument('-c',
                        '--container-for-m3u8',
                        choices=('ts', 'mp4'),
                        default='mp4',
                        help='A container for stream (m3u8) videos. '
                        'Default "mp4", a possible alternative is "ts".')

    parser.add_argument('-p',
                        '--save-parsed-download-urls',
                        action='store_true',
                        default=False,
                        help='Store urls in the file into user dir. '
                        'Filename has saving datetime so '
                        'this will not overwrite old links.')

    parser.add_argument('-nr',
                        '--no-restore-datetime',
                        action='store_true',
                        default=False,
                        help='The script trying to restore file creation date '
                        'before downloading to skip downloading '
                        'step for the files saved w/o datetime. '
                        'Pass the arg for skipping this step.')
    parser.add_argument('-v',
                        '--version',
                        action='store_true',
                        default=False,
                        help='Show the current script version')
    args = parser.parse_args()
    if args.version:
        print(f'The script version is {__version__}.')
        sys.exit(0)

    download_path = args.download_path
    if not download_path:
        download_path = os.environ.get(args.download_path_variable)
    download_path = download_path or '.'
    users = args.users + get_users_from_file(args.users_file_list)
    if not users:
        raise ValueError('There are no target users')
    else:
        logging.info(f'Target user count: %d', len(users))
    black_list_users = set(get_users_from_file('black_list_user_file'))
    if args.skip_existing and os.path.isdir(download_path):
        os.listdir(download_path)
        black_list_users |= set(os.listdir(download_path))
    if black_list_users:
        logging.info('Black list user count: %d', len(black_list_users))
    ffmpeg_bin = args.ffmpeg_bin
    disabled_content = args.disabled_content or []
    if 'all' in disabled_content:
        disabled_content = content_types[:-1]

    if not await VscoVideo.is_ffmpeg_exists(ffmpeg_bin):
        logging.info(
            "ffmpeg cant's be called with '%s'. "
            "Video content (m3u8) disabled!", ffmpeg_bin)
        disabled_content.append(VscoVideo.verbose_content_type)
    if len(disabled_content) == len(REGISTERED_CONTENT):
        msg = 'All content has been disabled'
        if not args.save_parsed_download_urls:
            raise ValueError(msg)
        logging.info("Only urls'll be save.")
    init_dict = {
        'download_limit': args.download_limit,
        'max_ffmpeg_threads': args.max_fmpeg_threads,
        'ffmpeg_bin': ffmpeg_bin,
        'disabled_content': set(disabled_content),
        'video_container': args.container_for_m3u8,
        'save_urls_to_file': args.save_parsed_download_urls,
        'restore_datetime': not args.no_restore_datetime
    }
    parse_dict = {
        'username_and_urls': users,
        'download_path': download_path,
        'black_list': black_list_users,
    }
    return init_dict, parse_dict
