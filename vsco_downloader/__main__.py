import asyncio
import datetime
import logging
import time
from typing import List

import aiohttp

from vsco_downloader.user import VscoUser
from .downloader import VscoGrabber


def parse_arg():
    pass


def prepare_links(link: str):
    if link.startswith('https://vsco.co/'):
        return link.split('https://vsco.co/')[-1].split('/')[0]
    return link


def main():
    logging.basicConfig(level=logging.INFO)
    grabber = VscoGrabber()

    users = []

    st_time = time.time()
    try:
        users: List[VscoUser] = asyncio.run(grabber.parse_users(users))
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


if __name__ == '__main__':
    main()
