import argparse
from banalcow import netbank, config, penny
from banalcow.logger import logger
from selenium.common.exceptions import WebDriverException
import sys
import time
import os
from pathlib import Path
import traceback


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--debug', 
        required=False, action='store_true', default=False,
        help='Debug'
    )
    parser.add_argument(
        '--only-home-loans', 
        required=False, action='store_true', default=False,
        help='Only process home loans'
    )
    parser.add_argument(
        '--penny', required=False, action='store_true', default=False,
        help='Import into penny'
    )
    parser.add_argument(
        '--netbank', required=False, action='store_true', default=False,
        help='Download netbank data'
    )
    parser.add_argument(
        '--retry', required=False, default=10, type=int,
        help='Number of attempts to retry'
    )
    parser.add_argument(
        '--sleep', required=False, default=30, type=int,
        help='The number of seconds to sleep'
    )
    return parser.parse_args()


def main():
    args = parse_args()
    conf = config.Config('./config.yml')

    if args.netbank:
        session = netbank.Netbank(
            conf.netbank.username, conf.netbank.password,
            chrome_driver_executable_path=conf.chrome_driver_executable_path,
            only_home_loans=args.only_home_loans, retry=args.retry,
            sleep=args.sleep, debug=args.debug
        )

        try:
            session.login()
        except WebDriverException as e:
            logger.error('Failed to login')
            logger.error(traceback.format_ext())
            session.driver.quit()
            sys.exit()

        accounts = session.get_accounts()

        for account, data in accounts.items():
            try:
                session.access_account(account, data.href)
            except WebDriverException as e:
                logger.error('Failed to access account')
                logger.error(traceback.format_ext())
                session.driver.quit()
                sys.exit()

            if data.account_type == netbank.AccountType.HOME_LOAN:
                session.view_transactions()

            session.download_ofx(data.filename, data.account_type)
            session.access_homepage()

        if not args.debug:
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
