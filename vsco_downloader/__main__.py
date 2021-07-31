import asyncio
import datetime
import logging
import time
from typing import List

from vsco_downloader.argparser import parse_arg
from vsco_downloader.user import VscoUser
from .downloader import VscoGrabber


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


def main():
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(a_main())
    except KeyboardInterrupt:
        logging.info('Finishing...')


if __name__ == '__main__':
    main()
