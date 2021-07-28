import asyncio
import datetime
import logging
import os
import re
import json
import tempfile
import time

import aiohttp
import aiofiles

from .container import VscoVideo
from .user import DEFAULT_LIMIT, VscoUser

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
                 content_limit=DEFAULT_LIMIT,
                 max_thread=25,
                 max_ffmpeg_concat=5,
                 content_dir='download'):
        self._content_dir = content_dir
        self._content_limit = content_limit

        self._logger = logging.getLogger('VSCO-GRABBER')
        self._loop = asyncio.get_event_loop()
        self._semaphore = asyncio.Semaphore(max_thread)
        self._max_ffmpeg_concat = asyncio.Semaphore(max_ffmpeg_concat)

    def _parse_first_page_content(self, html):
        result = re.search(
            r'<script>window.__PRELOADED_STATE__ = (.*)</script>', html)
        if not result:
            self._logger.warning('Oppps something going wrong... '
                                 'Was HTML structure changed?')
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
    async def _get_html_text(user: VscoUser, url):
        async with user.scrap_session.get(url) as request:
            content = await request.text()
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
        except KeyError as e:
            self._logger.error(e)
            return
        for media_dict in self._get_entries_dict(initial_json).values():
            user.add_content(media_dict)
        if not cursor and not user.all_content:
            self._logger.info('User %s has no content', user)
            return
        user.set_cursor(cursor)
        await self._parser_user_entries(user)

    async def _download_file(self, url, file_name, session):
        if not url:
            self._logger.warning('None url - skipped')
            return True
        if os.path.isfile(file_name):
            return

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
        out_file_name = file.get_file_name(self._content_dir, str(user))
        if os.path.isfile(out_file_name):
            return
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
                return None
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
                    # TODO: need to re-download w/o exit
                    self._logger.error('Error on downloading %s from %s', )
                    return False
            ffmpeg_cmd = file.generate_ffmpeg_concat(temp_files, out_file_name)
            async with self._max_ffmpeg_concat:
                error = await file.run_ffmpeg(ffmpeg_cmd)
            if error:
                self._logger.error('Error on concat %s: %s', out_file_name,
                                   error)
            else:
                self._logger.info('Video %s was downloaded', out_file_name)
            return error

    async def _download_user_content(self, user: VscoUser, content=None):
        all_content = content or user.all_content
        total_count = len(all_content)
        self._logger.info('Start downloading files for %s', user)
        async with aiohttp.ClientSession(
                headers=DEFAULT_HEADERS) as user.download_session:
            for index, file in enumerate(all_content.copy(), 1):
                async with self._semaphore:
                    if isinstance(file, VscoVideo):
                        downloaded = await self._download_large_file(
                            file, user)
                    else:
                        downloaded = await self._download_small_file(
                            file, user)
                if downloaded or downloaded is None:
                    all_content.remove(file)
                if not index % 10:
                    self._logger.info('%s: (%d/%d)', user, index, total_count)
        if not all_content:
            self._logger.info('All content (%d) downloaded for user %s',
                              total_count, user)
            return
        self._logger.warning('%d files were not downloaded. Retying...',
                             len(all_content))
        return await self._download_user_content(user, all_content)

    async def _parser_first_page(self, user):
        self._logger.info('Getting first page for %s', user)
        content = await self._get_html_text(user, user.user_url)
        self._logger.info('Parsing initial page content for %s', user)
        initial_json = self._parse_first_page_content(content)
        if not initial_json:
            return
        await self._parse_user_page(initial_json, user)
        return user

    async def parse_users(self, usernames):
        st_time = time.time()
        await asyncio.gather(
            *[self.parse_user(username) for username in usernames])
        delta = datetime.timedelta(seconds=time.time() - st_time)
        self._logger.info('Script finished in %s', delta)

    async def parse_user(self, username):
        vsco_user = VscoUser(username)
        async with aiohttp.ClientSession(
                headers=DEFAULT_HEADERS) as vsco_user.scrap_session:
            user = await self._parser_first_page(vsco_user)
            await self._download_user_content(user)
