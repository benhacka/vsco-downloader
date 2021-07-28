import asyncio
import logging

from .downloader import VscoGrabber


def parse_arg():
    pass


def main():
    logging.basicConfig(level=logging.INFO)
    grabber = VscoGrabber()
    users = []

    asyncio.run(grabber.parse_users(users))


if __name__ == '__main__':
    main()
