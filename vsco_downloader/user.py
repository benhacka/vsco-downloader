import urllib
from typing import Set

from vsco_downloader.container import VscoPhoto, VscoMiniVideo, VscoVideo, \
    VscoContent

DEFAULT_LIMIT = 14
BASE_URL = 'https://vsco.co/{user_name}/gallery'
CONTENT_URL = ('https://vsco.co/api/3.0/medias/profile?site_id={user_id}'
               '&limit={limit}'
               '&cursor={cursor}')


class VscoUser:
    def __init__(self, user_name):
        assert user_name
        self._user_name = user_name
        self._user_id = None
        self._photo_content: Set[VscoPhoto] = set()
        self._mini_video_content: Set[VscoMiniVideo] = set()
        self._video_content: Set[VscoVideo] = set()
        self._current_cursor = None
        self._finisher = False
        self._token = None
        self.download_session = None
        self.scrap_session = None

    def add_content(self, content_dict):
        content_class, content_set = {
            'photo': (VscoPhoto, self._photo_content),
            'mini_video': (VscoMiniVideo, self._mini_video_content),
            'video': (VscoVideo, self._video_content)
        }[VscoContent.get_content_type(content_dict)]
        content_set.add(content_class(content_dict))

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

    def __str__(self):
        return self._user_name