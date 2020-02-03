import argparse
from banalcow import netbank, config, penny
from banalcow.logger import logger
import sys
import time
import os
from pathlib import Path


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--penny', required=False, action='store_true', default=False,
        help='Import into penny'
    )
    parser.add_argument(
        '--netbank', required=False, action='store_true', default=False,
        help='Download netbank data'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    conf = config.Config('./config.yml')

    if args.netbank:
        session = netbank.Netbank(
            conf.netbank.username, conf.netbank.password,
            chrome_driver_executable_path=conf.chrome_driver_executable_path
        )
        session.login()
        accounts = session.accounts

        for account, data in accounts.items():
            session.access_account(account)
            if data.home_loan:
                session.view_transactions()
            session.download_ofx(data.filename)
            session.access_homepage()

        session.logout()
        session.driver.quit()

    if args.penny:
        try:
            chrome_driver = conf.chrome_driver_executable_path
            session = penny.Penny(
                conf.penny.base_url, conf.penny.username, conf.penny.password,
                chrome_driver_executable_path=chrome_driver
            )
        except AttributeError:
            logger.error('Failed to find Penny config in pass.')
            sys.exit()

        session.login()
        time.sleep(10)
        for path in Path('.').glob('*.ofx'):
            filename = str(path)
            logger.info(f'Uploading {filename}')
            session.upload(filename)
            os.remove(filename)

        session.logout()
        session.driver.quit()


if __name__ == '__main__':
    sys.exit(main())
