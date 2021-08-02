import asyncio
import logging
import os
import re
import json
import tempfile
from datetime import datetime
from glob import glob
from typing import List, Set

import aiohttp
import aiofiles

from vsco_downloader.container import VscoVideo, VscoPhoto, VscoMiniVideo
from vsco_downloader.user import VscoUser

DEFAULT_HEADERS = {
    'user-agent':
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
    '(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36',
    'accept':
    'text/html,application/xhtml+xml,application/xml;q=0.9,'
    'image/avif,image/webp,image/apng,*/*;'
    'q=0.8,application/signed-exchange;v=b3;q=0.9'
}


class VscoGrabber:
    def __init__(self,
                 *,
                 download_limit: int = 100,
                 max_ffmpeg_threads: int = 10,
                 ffmpeg_bin: str = 'ffmpeg',
                 disabled_content: Set[str] = None,
                 video_container='mp4',
                 save_urls_to_file=False,
                 restore_datetime=True):
        self._semaphore = asyncio.Semaphore(download_limit)
        self._max_ffmpeg_concat = asyncio.Semaphore(max_ffmpeg_threads)
        self._ffmpeg_bin = ffmpeg_bin
        self._disabled_content = disabled_content or {}
        self._video_container = video_container
        self._save_urls_to_file = save_urls_to_file
        self._restore_datetime = restore_datetime
        self._content_dir = '.'
        self._logger = logging.getLogger('VSCO-GRABBER')

    def _parse_first_page_content(self, html):
        result = re.search(
            r'<script>window.__PRELOADED_STATE__ = (.*)</script>', html)
        if not result:
            self._logger.warning('Initial JSON block were not found')
            return {}
        return json.loads(result.group(1))

    @staticmethod
    async def _get_json_with_auth(user):
        headers = {
            **user.scrap_session.headers, 'authorization':
            f'Bearer {user.token}'
        }
        async with user.scrap_session.get(user.get_content_link(),
                                          headers=headers) as request:
            content = await request.json()
            return content

    @staticmethod
    async def _get_html_text(user: VscoUser, url, return_also_url=False):
        async with user.scrap_session.get(url) as request:
            content = await request.text()
            if return_also_url:
                return content, request.url
            return content

    @staticmethod
    def _get_user_id(initial_json, user_name):
        try:
            return initial_json.get(
                'sites',
                {'siteByUsername': {
                    user_name: {
                        'site': {
                            'id': None
                        }
                    }
                }})['siteByUsername'][user_name]['site']['id']
        except KeyError:
            return None

    @staticmethod
    def _get_entries_dict(initial_json):
        return initial_json.get('entities', {'images': {}})['images']

    @staticmethod
    def _get_next_cursor(initial_json, user_id):
        media_dict = initial_json.get(
            'medias', {
                'bySiteId': {
                    str(user_id): {
                        'errorMsg':
                        'Media was not found or JSON structure changed!',
                        'nextCursor': None
                    }
                }
            })['bySiteId'][str(user_id)]
        error = media_dict.get('errorMsg')
        if error:
            raise KeyError(error)
        return media_dict['nextCursor']

    @staticmethod
    def _get_token(initial_json):
        return initial_json.get('users', {'currentUser': {
            'tkn': None
        }})['currentUser']['tkn']

    async def _parser_user_entries(self, user):
        counter = 1
        while user.cursor:
            try:
                content = await self._get_json_with_auth(user)
            finally:
                user.clear_cursor()
            user.set_cursor(content.get('next_cursor'))
            media = content.get('media', [])
            for image_dict in media:
                user.add_content(image_dict[image_dict['type']])
            self._logger.info('Page %d parsed for %s. Total content: %d',
                              counter, user, len(user.all_content))
            counter += 1

    async def _parse_user_page(self, initial_json, user: VscoUser):
        try:
            user_id = self._get_user_id(initial_json, str(user))
            if not user_id:
                self._logger.error("Can't parse site_id for %s", user)
                return
            user.set_user_id(user_id)
            token = self._get_token(initial_json)
            if not token:
                self._logger.error("Can't parse Bearer token for %s", user)
                return
            user.set_token(token)
            try:
                cursor = self._get_next_cursor(initial_json, user_id)
            except KeyError:
                self._logger.error('Getting cursor error for %s', user)
                return
            for media_dict in self._get_entries_dict(initial_json).values():
                user.add_content(media_dict)
            if not cursor and not user.all_content:
                self._logger.info('User %s has no content', user)
                return
            user.set_cursor(cursor)
        finally:
            if user.cursor is None and not user.all_content:
                user.set_invalid()
            user.set_initialized()

    async def _download_file(self, url, file_name, session):
        if not url:
            self._logger.warning('None url for %s', file_name)
            return False
        if os.path.isfile(file_name):
            return None

        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        try:
            async with session.get(url) as request:
                async with aiofiles.open(file_name, 'wb') as file:
                    await file.write(await request.read())
                    return True
        except aiohttp.ClientError as e:
            self._logger.error(e)
        return False

    async def _download_small_file(self, file, user):
        return await self._download_file(
            file.download_url, file.get_file_name(self._content_dir,
                                                  str(user)),
            user.download_session)

    async def _download_large_file(self, file: VscoVideo, user: VscoUser):
        out_file_name = file.get_file_name(self._content_dir,
                                           str(user),
                                           container=self._video_container)
        if os.path.isfile(out_file_name):
            return None
        with tempfile.TemporaryDirectory() as tmp_dir_name:
            file.set_temp_dir(tmp_dir_name)
            try:
                parted_url_text = await self._get_html_text(
                    user, file.download_url)
            except aiohttp.ClientError as e:
                self._logger.error('Error on getting m3u8 for a file %s: %s',
                                   out_file_name, e)
                return False
            parted_url = file.choice_best_resolution(parted_url_text)
            if not parted_url:
                self._logger.error(
                    'Cant parser best resolution url for a file %s. '
                    'Skipping...', out_file_name)
                return False
            parted_urls_text = await self._get_html_text(user, parted_url)
            parted_urls = re.findall(r'http[s]?://.*', parted_urls_text)
            content_temp_dir = file.temp_content_dir
            os.makedirs(content_temp_dir, exist_ok=True)
            temp_files = []
            for url in parted_urls:
                file_name = url.split('?')[0].split('/')[-1]
                file_name = os.path.join(content_temp_dir, file_name)
                if (await self._download_file(url, file_name,
                                              user.download_session)):
                    temp_files.append(file_name)
                else:
                    self._logger.error('Error on downloading %s from %s', )
                    return False
            ffmpeg_cmd = file.generate_ffmpeg_concat(self._ffmpeg_bin,
                                                     temp_files, out_file_name,
                                                     self._video_container)
            async with self._max_ffmpeg_concat:
                error = await file.run_ffmpeg(ffmpeg_cmd)
            if error:
                self._logger.error('Error on concat %s: %s', out_file_name,
                                   error)
                return False
            self._logger.info('Video %s was downloaded', out_file_name)
            return True

    async def _download_user_content(self, user: VscoUser):
        all_content = user.all_content
        total_count = len(all_content)
        if not total_count:
            self._logger.info('User %s has no content', user)
            return
        user_dir = os.path.join(self._content_dir, str(user))
        if self._save_urls_to_file:
            os.makedirs(user_dir, exist_ok=True)
            log_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S_urls.txt")
            log_name = os.path.join(user_dir, log_name)
            async with aiofiles.open(log_name, 'w') as log_file:
                await log_file.write('\n'.join(
                    [str(file.download_url) for file in all_content]))
        photo_verbose, video_verbose = [
            content.verbose_content_type
            for content in (VscoPhoto, VscoMiniVideo)
        ]
        rename_dict = {photo_verbose: set(), video_verbose: set()}
        if self._restore_datetime:
            rename_dict = self._get_rename_dict(user_dir, photo_verbose,
                                                video_verbose)
        self._logger.info('Start downloading files for %s', user)
        async with aiohttp.ClientSession(
                headers=DEFAULT_HEADERS) as user.download_session:
            for index, file in enumerate(all_content.copy(), 1):
                content_type = file.verbose_content_type
                need_to_rename = (file.get_original_name()
                                  in rename_dict.get(content_type, set()))
                if need_to_rename:
                    self._rename_file(file, user_dir)
                if file.verbose_content_type in self._disabled_content:
                    user.stat.add_skipped(file)
                    continue
                async with self._semaphore:
                    if isinstance(file, VscoVideo):
                        downloaded = await self._download_large_file(
                            file, user)
                    else:
                        downloaded = await self._download_small_file(
                            file, user)
                if downloaded:
                    user.stat.add_downloaded(file)
                elif downloaded is None:
                    user.stat.add_skipped(file)

                if not index % 10:
                    self._logger.info('%s: (%d / %d)', user, index,
                                      total_count)

    @staticmethod
    def _find_files_with_out_date(
        path,
        extension,
    ):
        match_pattern = r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}_.*?'
        files = {
            os.path.basename(file)
            for file in glob(f'{path}/*.{extension}')
        }
        if not files:
            return set(), 0
        content_set = set(
            filter(lambda file: not re.match(match_pattern, file), files))
        return content_set, len(content_set)

    def _get_rename_dict(self, user_dir, photo_key, video_key):
        rename_dict = {photo_key: set(), video_key: set()}
        photo_count = video_count = 0
        if VscoPhoto.verbose_content_type not in self._disabled_content:
            rename_dict[
                photo_key], photo_count = self._find_files_with_out_date(
                    user_dir, 'jpg')
        if VscoVideo.verbose_content_type not in self._disabled_content:
            rename_dict[
                video_key], video_count = self._find_files_with_out_date(
                    user_dir, 'mp4')
        common_warn = 'Detected %d %s with out datetime in the %s'
        if photo_count:
            self._logger.warning(common_warn, photo_count, 'photos', user_dir)
        if photo_count:
            self._logger.warning(common_warn, video_count, 'videos', user_dir)
        return rename_dict

    def _rename_file(self, file, user_dir):
        origin_name = file.get_file_name(user_dir, datetime_prefix=False)
        name_with_datetime = file.get_file_name(user_dir)
        try:
            os.rename(origin_name, name_with_datetime)
            self._logger.info(f"Renamed file '%s' with out datetime to '%s'",
                              origin_name, name_with_datetime)
            return True
        except OSError as e:
            self._logger.error("Can't renamed a file '%s' to '%s': %s",
                               origin_name, name_with_datetime, e)
            return False

    async def _parser_first_page(self, user):
        try:
            is_short_init = user.is_inited_with_short
            logger_add = ('and username from' if is_short_init else 'for')
            self._logger.info('Getting first page %s %s', logger_add, user)
            if is_short_init:
                url = user.inited_arg
                content, full_url = await self._get_html_text(user, url, True)
                user_name, is_full_url = user.get_username_from_full_url(
                    str(full_url))
                user.set_username(user_name)
                self._logger.info('Mapped username %s for url %s', user_name,
                                  url)
                if not is_full_url:
                    self._logger.info(
                        'Url %s is content link. First init skipped', url)
                    user.clear_init_with_short()
                    return
            else:
                content = await self._get_html_text(user, user.user_url)

        except aiohttp.ClientError as e:
            user.set_invalid()
            self._logger.error('Error on parse page %s', e)
            return
        self._logger.info('Parsing initial page content for %s', user)
        initial_json = self._parse_first_page_content(content)
        if not initial_json:
            user.set_invalid()
            return
        await self._parse_user_page(initial_json, user)

    def _get_splitted_user_sets(self, usernames_and_urls):
        usernames = set()
        short_urls = set()
        for url_username in usernames_and_urls:
            if not url_username.strip():
                continue
            if 'vsco.co/' in url_username:
                try:
                    user_name, _ = VscoUser.get_username_from_full_url(
                        url_username)
                except ValueError as e:
                    self._logger.info(e)
                    continue
                usernames.add(user_name)
            elif 'vs.co/' in url_username:
                short_urls.add(url_username)
            else:
                if not VscoUser.is_valid_username(url_username):
                    self._logger.warning(
                        '%s is not vsco url and incorrect username. Skipped!',
                        url_username)
                    continue
                usernames.add(url_username)
        return usernames, short_urls

    async def _restore_users(self, usernames_and_urls: Set[str], session,
                             black_list: Set[str]) -> List[VscoUser]:
        usernames, short_urls = self._get_splitted_user_sets(
            usernames_and_urls)
        bl_usernames, bl_short_urls = self._get_splitted_user_sets(black_list)
        if bl_short_urls:
            self._logger.warning('Black list contains short links. '
                                 'They will be ignored!')
        source_len = len(usernames)
        usernames -= bl_usernames
        if len(usernames) != source_len:
            self._logger.info(
                '%d blacklisted users have '
                'been removed from targets', source_len - len(usernames))
        if not short_urls:
            self._logger.debug('There are no short links')
            return [VscoUser(username, session) for username in usernames]
        self._logger.info(f'Inited %d users with short url', len(short_urls))
        pre_inited_users = [
            VscoUser(short_url, session, True) for short_url in short_urls
        ]
        inited_users: List[VscoUser] = await asyncio.gather(
            *[self.parse_user(user, True) for user in pre_inited_users])
        for user in inited_users:
            repeat = str(user) in usernames
            if repeat:
                usernames.remove(str(user))
                self._logger.info(
                    'Removed %s from usernames. '
                    'This username grabbed with short', user)
        return inited_users + [
            VscoUser(user_name, session) for user_name in usernames
        ]

    async def parse_users(self,
                          username_and_urls: Set[str],
                          download_path='.',
                          black_list=None):
        async with aiohttp.ClientSession(
                headers=DEFAULT_HEADERS) as scrap_session:
            self._content_dir = download_path
            users = await self._restore_users(username_and_urls, scrap_session,
                                              (black_list or {}))
            if not users:
                self._logger.warning(
                    'There are no users for download. Stopping...')
                return []
            try:
                users = await asyncio.gather(
                    *[self.parse_user(user) for user in users])
            except (KeyboardInterrupt, asyncio.CancelledError):
                self._logger.info('Stopping...')
        return users

    async def parse_user(self, vsco_user: VscoUser, only_init=False):
        if vsco_user.is_invalid:
            return vsco_user
        if not vsco_user.is_inited:
            await self._parser_first_page(vsco_user)
        if not only_init and not vsco_user.is_invalid:
            await self._parser_user_entries(vsco_user)
            await self._download_user_content(vsco_user)
        return vsco_user
