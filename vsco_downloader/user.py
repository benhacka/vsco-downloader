import re
import urllib
from typing import Set, Type, Dict

from vsco_downloader.container import (VscoPhoto, VscoMiniVideo, VscoVideo,
                                       VscoContent)

DEFAULT_LIMIT = 14
BASE_URL = 'https://vsco.co/{user_name}/gallery'
CONTENT_URL = ('https://vsco.co/api/3.0/medias/profile?site_id={user_id}'
               '&limit={limit}'
               '&cursor={cursor}')


class VscoContentStat:
    def __init__(self, content_type: Type[VscoContent]):
        self._verbose_content_type = content_type.verbose_content_type
        self._total_count = 0
        self._downloaded_count = 0
        self._skipped_count = 0

    def add_total(self, count):
        self._total_count += count

    def add_downloaded(self, count):
        self._downloaded_count += count

    def add_skipped(self, count):
        self._skipped_count += count

    @property
    def error_count(self):
        return (self._total_count - self._downloaded_count -
                self._skipped_count)

    @property
    def verbose_string(self):
        if not self._total_count:
            return ''
        stat_string = f'{self._verbose_content_type}: '
        if self._skipped_count == self._total_count:
            stat_string += f'All files ({self._total_count}) skipped'
        elif self._downloaded_count == self._total_count:
            stat_string += f'All files ({self._total_count}) downloaded'
        elif self.error_count == self._total_count:
            stat_string += (
                f'All files ({self._total_count}) not finished - error!')
        else:
            skip = self._skipped_count / self._total_count
            download = self._downloaded_count / self._total_count
            error = self.error_count / self._total_count
            stat_string += (
                f'Downloaded {download:.2%} ({self._downloaded_count}), '
                f'Skipped {skip:.2%} ({self._skipped_count})')
            if self.error_count:
                stat_string += f', Errors: {error:.2%} ({self.error_count})'
        return stat_string


class VscoUserStat:
    def __init__(self):
        self._content: Dict[str, VscoContentStat] = {
            content_type.verbose_content_type: VscoContentStat(content_type)
            for content_type in (VscoPhoto, VscoMiniVideo, VscoVideo)
        }

    def add_total(self, content_type, count=1):
        self._content[content_type.verbose_content_type].add_total(count)

    def add_downloaded(self, content_type, count=1):
        self._content[content_type.verbose_content_type].add_downloaded(count)

    def add_skipped(self, content_type, count=1):
        self._content[content_type.verbose_content_type].add_skipped(count)

    @property
    def all_content_stat(self):
        stat_list = [stat.verbose_string for stat in self._content.values()]
        stat_string = ' | '.join([stat for stat in stat_list if stat])
        if stat_string:
            return f'[{stat_string}]'
        return 'user not found or has no content'

    @property
    def has_error(self):
        return any([stat.error_count for stat in self._content.values()])


class VscoUser:
    reg_exp_username = r'^[A-Za-z0-9_-]*$'
    allowed_vsco_path = ('', 'media', 'gallery', 'video')

    def __init__(self,
                 username_or_short_url,
                 session,
                 init_with_short_url=False):
        assert username_or_short_url
        self._user_name = username_or_short_url
        self.scrap_session = session
        self._init_with_short_url = init_with_short_url
        self._user_id = None
        self._photo_content: Set[VscoPhoto] = set()
        self._mini_video_content: Set[VscoMiniVideo] = set()
        self._video_content: Set[VscoVideo] = set()
        self._current_cursor = None
        self._finisher = False
        self._token = None
        self.download_session = None
        self._invalid_account = False
        self._init_content_parsed = False
        self._vsco_user_stat = VscoUserStat()

    @property
    def inited_arg(self):
        return self._user_name

    @property
    def is_inited_with_short(self):
        return self._init_with_short_url

    @property
    def stat(self) -> VscoUserStat:
        return self._vsco_user_stat

    @property
    def stat_string(self):
        return f'{self._user_name}: {self._vsco_user_stat.all_content_stat}'

    @property
    def is_inited(self):
        return self._init_content_parsed

    @property
    def is_invalid(self):
        return self._invalid_account

    @property
    def cursor(self):
        return self._current_cursor

    @property
    def token(self):
        return self._token

    @property
    def all_content(self):
        return (self._photo_content | self._mini_video_content
                | self._video_content)

    @property
    def user_url(self):
        return BASE_URL.format(user_name=self._user_name)

    def set_username(self, user_name):
        self._user_name = user_name

    def add_content(self, content_dict, force_ignored_content=None):
        force_ignored_content = force_ignored_content or {}
        content_class = VscoContent.get_content_type(content_dict)
        if content_class.verbose_content_type in force_ignored_content:
            return
        content_set = {
            VscoPhoto: self._photo_content,
            VscoMiniVideo: self._mini_video_content,
            VscoVideo: self._video_content
        }[content_class]
        self.stat.add_total(content_class)
        content_set.add(content_class(content_dict))

    def set_initialized(self):
        self._init_content_parsed = True

    def set_invalid(self):
        self._invalid_account = True

    def clear_init_with_short(self):
        self._init_with_short_url = False

    def get_content_link(self, limit=DEFAULT_LIMIT):
        assert self._user_id
        assert self._current_cursor
        return CONTENT_URL.format(user_id=self._user_id,
                                  limit=limit,
                                  cursor=urllib.parse.quote_plus(
                                      self._current_cursor))

    def set_user_id(self, user_id):
        self._user_id = user_id

    def set_cursor(self, cursor):
        self._current_cursor = cursor

    def clear_cursor(self):
        self._current_cursor = None

    def set_token(self, token):
        self._token = token

    @classmethod
    def parse_content_link(cls, url):
        possible_q_keys = ['link_name']
        qs_dict = urllib.parse.parse_qs(url)
        for q_key in possible_q_keys:
            if q_key in qs_dict:
                return qs_dict[q_key][0]
        raise ValueError(f"Can't parse username from query of {url}")

    @classmethod
    def get_username_from_full_url(cls, full_url: str):
        """ 
        :return: Tuple[username], is_full (False if it's a content url)
        or raise ValueError 
        """
        is_full = True
        if not full_url.endswith('/'):
            full_url += '/'
        full_url = full_url.replace('vsco.co:443', 'vsco.co')
        username, *trail = full_url.split('vsco.co/')[-1].split('/')
        if len(trail):
            trail = trail[0]
            is_full = False
        if not username or (trail and trail not in cls.allowed_vsco_path):
            raise ValueError(f'Incorrect url {full_url}')
        if cls.is_valid_username(username):
            return username, is_full
        return cls.parse_content_link(full_url), False

    @classmethod
    def is_valid_username(cls, username):
        return re.match(cls.reg_exp_username, username) is not None

    def __str__(self):
        return self._user_name
