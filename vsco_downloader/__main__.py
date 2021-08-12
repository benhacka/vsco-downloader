import asyncio
import datetime
import logging
import sys
import time
from functools import wraps
from typing import List
from asyncio.proactor_events import _ProactorBasePipeTransport

from vsco_downloader.argparser import parse_arg
from vsco_downloader.user import VscoUser
from vsco_downloader.downloader import VscoGrabber


def py_version_checker():
    min_major, min_minor = (3, 7)
    if sys.version_info < (min_major, min_minor):
        sys.exit(f'Python < {min_major}.{min_minor} is not supported')


async def a_main():
    try:
        init_dict, parse_dict = await parse_arg()
    except ValueError as e:
        logging.error(e)
        return
    grabber = VscoGrabber(**init_dict)

    st_time = time.time()
    try:
        users: List[VscoUser] = await grabber.parse_users(**parse_dict)
        stat_logger = logging.getLogger('Stat')
        for user in users:
            log = (stat_logger.warning if user.stat.has_error
                   or user.is_invalid else stat_logger.info)
            log(user.stat_string)
    except (KeyboardInterrupt, asyncio.CancelledError):
        logging.info('Script canceled. Finishing...')
    finally:
        delta = datetime.timedelta(seconds=time.time() - st_time)
        logging.info('Script finished in %s', delta)


def patch_false_positive_runtime_error():
    """yeah this is fucking kludge only for wi[o]n-boyz"""
    def silence_event_loop_close(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except RuntimeError as e:
                if str(e) != 'Event loop is closed':
                    raise

        return wrapper

    _ProactorBasePipeTransport.__del__ = silence_event_loop_close(
        _ProactorBasePipeTransport.__del__)
    # logging.warning(
    #     'A _ProactorBasePipeTransport.__del__ patched w/ kludge...')


def main():
    py_version_checker()
    logging.basicConfig(level=logging.INFO)
    is_new_ver_and_win = (sys.version_info[0] == 3 and sys.version_info[1] >= 8
                          and sys.platform.startswith('win'))
    if is_new_ver_and_win:
        patch_false_positive_runtime_error()
    try:
        asyncio.run(a_main())
    except KeyboardInterrupt:
        logging.info('Finishing...')


if __name__ == '__main__':
    main()
