import asyncio
import datetime
import logging
import os
import re
from abc import ABC
from pprint import pprint
from typing import Type, Union


class VscoContent(ABC):
    verbose_content_type = None

    def __init__(self, content_dict):
        self._content_dict = content_dict

    @property
    def download_url(self):
        raise NotImplementedError

    @property
    def datetime(self):
        capture_date = (self._content_dict.get('captureDate')
                        or self._content_dict.get('capture_date')
                        or self._content_dict.get('created_date')
                        or self._content_dict.get('uploadDate')
                        or self._content_dict.get('last_updated'))
        if not capture_date:
            logging.getLogger('Content').warning(
                'Datetime were not found in %s', str(self._content_dict))
            return ''
        return datetime.datetime.fromtimestamp(
            capture_date / 1000).strftime("%Y-%m-%d_%H-%M-%S_")

    def get_file_name(self, *download_path):
        if not self.download_url:
            return None
        name = self.download_url.split('/')[-1]
        return os.path.join(*download_path, f'{self.datetime}{name}')

    @classmethod
    def get_content_type(
        cls, content_dict
    ) -> Union[Type['VscoPhoto'], Type['VscoMiniVideo'], Type['VscoVideo'], ]:
        if 'videoUrl' in content_dict or 'video_url' in content_dict:
            return VscoMiniVideo
        if 'playback_url' in content_dict:
            return VscoVideo
        return VscoPhoto


class VscoPhoto(VscoContent):
    verbose_content_type = 'photo'

    @property
    def download_url(self):
        try:
            return 'https://' + (self._content_dict.get('responsiveUrl')
                                 or self._content_dict.get('responsive_url'))
        except TypeError:
            pprint(self._content_dict)
            return None


class VscoMiniVideo(VscoContent):
    verbose_content_type = 'mini-video'

    @property
    def download_url(self):
        return 'https://' + (self._content_dict.get('videoUrl')
                             or self._content_dict.get('video_url'))


class VscoVideo(VscoContent):
    verbose_content_type = 'video'

    def __init__(self, content_dict):
        self._temp_dir = None
        super().__init__(content_dict)

    def set_temp_dir(self, temp_dir):
        self._temp_dir = temp_dir

    @property
    def download_url(self):
        return self._content_dict['playback_url']

    def get_file_name(self, *download_path):
        if not self.download_url:
            return None
        # TODO: make container as param
        name = self._content_dict['_id'] + '.mp4'
        return os.path.join(*download_path, f'{self.datetime}{name}')

    @classmethod
    def choice_best_resolution(cls, m3u8_text):
        res_dict = {}
        splitted_lines = m3u8_text.splitlines()
        for index, line in enumerate(splitted_lines):
            ext_string = (re.search(r'RESOLUTION=(\d*)x\d*', line))
            if not ext_string:
                continue
            res_dict[int(ext_string.group(1))] = splitted_lines[index + 1]
        return res_dict[max(res_dict)]

    def generate_ffmpeg_concat(self, files, out_file):
        concat_string = self._generate_concat_string(files)
        ffmpeg_cmd = (f'ffmpeg -hide_banner -loglevel error -y -i '
                      f'"{concat_string}" -c copy -bsf:a aac_adtstoasc '
                      f'{out_file}')
        return ffmpeg_cmd

    @staticmethod
    async def run_ffmpeg(ffmpeg_cmd):
        proc = await asyncio.create_subprocess_shell(
            ffmpeg_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,)
        stdout, stderr = await proc.communicate()
        return stderr.decode() if stderr else None

    @classmethod
    async def is_ffmpeg_exists(cls):
        # TODO: make ffmpeg bin alias as param
        return not cls.run_ffmpeg('ffmpeg -version')

    def _generate_concat_string(self, files):
        return 'concat:' + '|'.join(
            (os.path.join(self.temp_content_dir, file) for file in files))

    @property
    def temp_content_dir(self):
        assert self._temp_dir
        return os.path.join(self._temp_dir,
                            self.download_url.split('/')[-1].split('.')[0])
