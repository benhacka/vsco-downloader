import asyncio
import datetime
import logging
import time
from typing import List

from vsco_downloader.user import VscoUser
from .downloader import VscoGrabber


def parse_arg():
    pass


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
