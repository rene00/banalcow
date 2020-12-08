from collections import namedtuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, WebDriverException,
    TimeoutException, StaleElementReferenceException
)
import datetime
import time
import shutil
import os
from enum import Enum, unique
from banalcow import banalutil
from banalcow.driver import BanalDriver


class NetbankError(Exception):
    pass


class FileNotFoundError(OSError):
    pass

@unique
class AccountType(Enum):
    HOME_LOAN = 1
    COMPLETE_ACCESS = 2
    CREDIT_CARD = 3
    MISA = 4


class Netbank:
    login_url = "https://www.my.commbank.com.au/netbank/Logon/Logon.aspx"
    date_fmt = "%d/%m/%Y"

    def __init__(self, username, password, sleep, retry, **kwargs):
        self.username = username
        self.password = password
        self.sleep = sleep
        self.retry = retry
        self.from_date = kwargs.get('from_date')
        self.to_date = kwargs.get('to_date')
        self.proxy = kwargs.get('proxy')
        self.chrome_driver_executable_path = kwargs.get(
            'chrome_driver_executable_path'
        )
        self.only_home_loans = kwargs.get('only_home_loans', False)
        self.debug = kwargs.get('debug', False)


        if self.__from_date > self.__to_date:
            raise NetbankError(
                "{0} is greater than {1}".
                format(self.__from_date, self.__to_date)
            )

        self.bd = BanalDriver(
            chrome_driver_executable_path=self.chrome_driver_executable_path,
            proxy=self.proxy,
        )
        self.driver = self.bd.driver

    @property
    def today(self):
        return datetime.datetime.now()

    @property
    def last_year(self):
        return banalutil.pastdt()

    @property
    def from_date(self):
        return self.__from_date

    @from_date.setter
    def from_date(self, from_date):
        if from_date is None:
            self.__from_date = self.last_year
        else:
            try:
                self.__from_date = datetime.datetime.strptime(
                    from_date, self.date_fmt
                )
            except ValueError:
                raise NetbankError(
                    "{0} does not match {1}".format(from_date, self.date_fmt)
                )

    @property
    def to_date(self):
        return self.__to_date

    @to_date.setter
    def to_date(self, to_date):
        if to_date is None:
            self.__to_date = self.today
        else:
            try:
                self.__to_date = datetime.datetime.strptime(
                    to_date, self.date_fmt
                )
            except ValueError:
                raise NetbankError(
                    "{0} does not match {1}".format(to_date, self.date_fmt)
                )

    def login(self):
        self.driver.get(self.login_url)
        user_field = self.driver.find_element_by_id('txtMyClientNumber_field')
        password_field = self.driver.find_element_by_id('txtMyPassword_field')
        submit_button = self.driver.find_element_by_id('btnLogon_field')
        user_field.send_keys(self.username)
        password_field.send_keys(self.password)
        submit_button.click()
        self.homepage = self.driver.current_url

    def get_accounts(self):
        """Account information in the form of a dict of tuples."""

        # Use WebDriverWait to wait for the presence of the portfolio table.
        # This was taking a bit too long to render sometimes and selenium would
        # throw an exception not being able to find the element in time.
        WebDriverWait(self.driver, self.sleep).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="StartMainContent"]/div/div[2]/div[1]/main/section[1]/div/div[1]')
            )
        )

        account = namedtuple(
            'account',
            'name balance available href filename account_type'
        )

        accounts = {}
        count = 1
        while True:
            account_type = None

            try:
                self.driver.find_element_by_xpath('//*[@id="StartMainContent"]/div/div[2]/div[1]/main/section[1]/div/div[1]/div[{0}]'.format(count))
            except NoSuchElementException:
                break

            name = self.driver.find_element_by_xpath('//*[@id="StartMainContent"]/div/div[2]/div[1]/main/section[1]/div/div[1]/div[{0}]/div/div[1]/div[2]/div/div/div/a/h3'.format(count))

            if name.get_attribute('title').lower() == 'commsec shares':
                count += 1
                continue

            if name.get_attribute('title').lower() == 'home loan':
                account_type = AccountType.HOME_LOAN
            elif name.get_attribute('title').lower() == 'complete access':
                account_type = AccountType.COMPLETE_ACCESS
            elif name.get_attribute('title').lower() == 'mastercard platinum':
                account_type = AccountType.CREDIT_CARD
            elif name.get_attribute('title').lower() == 'misa':
                account_type = AccountType.MISA

            if self.only_home_loans and account_type != AccountType.HOME_LOAN:
                count += 1
                continue

            number = self.driver.find_element_by_xpath('//*[@id="StartMainContent"]/div/div[2]/div[1]/main/section[1]/div/div[1]/div[{0}]/div/div[1]/div[2]/div/div/span/div'.format(count))
            balance = self.driver.find_element_by_xpath('//*[@id="StartMainContent"]/div/div[2]/div[1]/main/section[1]/div/div[1]/div[{0}]/div/div[1]/div[2]/div/ul/li[1]/span[2]'.format(count))
            available = self.driver.find_element_by_xpath('//*[@id="StartMainContent"]/div/div[2]/div[1]/main/section[1]/div/div[1]/div[{0}]/div/div[1]/div[2]/div/ul/li[2]/span[2]'.format(count))
            href = self.driver.find_element_by_xpath('//*[@id="StartMainContent"]/div/div[2]/div[1]/main/section[1]/div/div[1]/div[{0}]/div/div[1]/div[2]/div/div/div/a'.format(count))

            # Remove all non-digits from account number
            accountnumber = ''.join(filter(str.isdigit, number.text))

            if accounts.get(accountnumber):
                count += 1
                continue

            filename = banalutil.filename(
                accountnumber, self.from_date, self.to_date
            )

            if self.debug:
                print(
                    "DEBUG1: {0},{1},{2},{3},{4},{5},{6}".format(
                        name.get_attribute('title'),
                        accountnumber,
                        balance.get_attribute('title'),
                        available.get_attribute('title'),
                        href.get_attribute('href'),
                        filename,
                        account_type
                    )
                )

            accounts[accountnumber] = account(
                name=name.get_attribute('title'),
                balance=balance.get_attribute('title'),
                available=available.get_attribute('title'),
                href=href.get_attribute('href'),
                filename=filename,
                account_type=account_type
            )

            count += 1

        return accounts

    def logout(self):
        attempts = 0
        while attempts < self.retry:
            attempts += 1
            try:
                logout = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id=header]/div[2]/nav/div[1]/ul/li[3]')
                    )
                )
            except TimeoutException:
                break

            try:
                logout.click()
            except StaleElementReferenceException:
                pass
            else:
                break

    def access_homepage(self):
        self.driver.get(self.homepage)

    def access_account(self, accountnumber, href):
        self.driver.get(href)

    def view_transactions(self):
        """ Click the view transctions link within the Home Loan
        accounts page

        Non Home Loan accounts dont have this link.
        """
        attempts = 0
        while (attempts < self.retry):
            attempts += 1
            try:
                search_elem = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="lnk-transactions-viewAll"]')

                    )
                )
            except TimeoutException:
                break

            try:
                search_elem.click()
            except StaleElementReferenceException:
                pass
            else:
                break

    def download_ofx(self, filename, account_type):
        attempts = 0
        while (attempts < self.retry):
            attempts += 1
            try:
                element_xpath = '//*[@id="ctl00_CustomFooterContentPlaceHolder_updatePanelExport1"]/div'
                if account_type == AccountType.COMPLETE_ACCESS:
                    element_xpath = '//*[@id="export-link"]'
                export_elem = WebDriverWait(self.driver, self.sleep).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            element_xpath
                        )
                    )
                )
            except (
                NoSuchElementException,
                WebDriverException,
                TimeoutException
            ) as e:
                if self.debug:
                    print(e)

                if attempts == self.retry:
                    if not self.debug:
                        session.logout()
                        self.driver.quit()
                    raise NetbankError("Unable to find export element")
            else:
                export_elem.click()
                break

        """
        try:
            export_type_elem = Select(
                self.driver.find_element_by_xpath(
                    '//*[@id="ctl00_CustomFooterContentPlaceHolder_ddlExportType1_field"]'

                )
            )
        except (NoSuchElementException, WebDriverException) as e:
            print(e)
        else:
            export_type_elem.select_by_value('OFX')
        """

        try:
            if account_type == AccountType.COMPLETE_ACCESS:
                export_type_elem = self.driver.find_element_by_xpath(
                    '//*[@id="export-format-type"]/div/div[2]/label'
                )
            else:
                export_type_elem = Select(
                    self.driver.find_element_by_xpath(
                        '//*[@id="ctl00_CustomFooterContentPlaceHolder_ddlExportType1_field"]'

                    )
                )
        except (NoSuchElementException, WebDriverException) as e:
            print(e)
        else:
            if account_type == AccountType.COMPLETE_ACCESS:
                export_type_elem.click()
            else:
                export_type_elem.select_by_value('OFX')


        try:
            submit_button_xpath = '//*[@id="ctl00_CustomFooterContentPlaceHolder_lbExport1"]'
            if account_type == AccountType.COMPLETE_ACCESS:
                submit_button_xpath = '//*[@id="txnListExport-submit-btn"]'
            submit_button = self.driver.find_element_by_xpath(submit_button_xpath)
        except (NoSuchElementException, WebDriverException) as e:
            print(e)
        else:
            submit_button.click()

        ofxdata_filename = 'OFXData.ofx'
        count = 1
        while not os.path.exists(ofxdata_filename):
            time.sleep(1)
            if count > self.retry:
                raise NetbankError(
                    "Unable to find file {0}".
                    format(filename)
                )
            count += 1
        shutil.move(ofxdata_filename, filename)
