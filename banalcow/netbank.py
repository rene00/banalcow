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
from IPython import embed
from banalcow import banalutil
from banalcow.driver import BanalDriver


class NetbankError(Exception):
    pass


class FileNotFoundError(OSError):
    pass


class Netbank:
    login_url = "https://www.my.commbank.com.au/netbank/Logon/Logon.aspx"
    date_fmt = "%d/%m/%Y"

    def __init__(self, username, password, **kwargs):
        self.username = username
        self.password = password
        self.from_date = kwargs.get('from_date')
        self.to_date = kwargs.get('to_date')
        self.proxy = kwargs.get('proxy')
        self.chrome_driver_executable_path = kwargs.get(
            'chrome_driver_executable_path'
        )

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

    @property # noqa[C901]
    def accounts(self):
        """Account information in the form of a dict of tuples."""

        # Use WebDriverWait to wait for the presence of the portfolio table.
        # This was taking a bit too long to render sometimes and selenium would
        # throw an exception not being able to find the element in time.
        table = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, '//*[@id="MyPortfolioGrid1_a"]')
            )
        )

        accounts = {}
        account = namedtuple(
            'account',
            'nickname balance funds href filename home_loan'
        )

        for row in table.find_elements_by_xpath(".//tr"):
            bsb = None
            home_loan = False
            for td in row.find_elements(By.TAG_NAME, 'td'):
                _class = td.get_attribute('class')
                if _class == 'BSBField':
                    bsb = td.text.replace(' ', '')
                elif _class == 'AccountNumberField':
                    accountnumber = td.text.replace(' ', '')
                elif _class == 'NicknameField FirstCol':
                    nickname = td.text
                    div = td.find_elements_by_xpath(
                        '//*[@id="{0}"]/div/div[1]'.
                        format(td.get_attribute('id'))
                    )[0]
                    anchor = div.find_elements_by_xpath('.//a')[0]
                    href = anchor.get_attribute('href')
                elif _class == ('AccountBalanceField CurrencyField '
                                'CurrencyFieldBold'):
                    balance = td.text
                elif _class == 'AvailableFundsField CurrencyField LastCol':
                    funds = td.text

            # If bsb can be coerced into an int, we are dealing with an
            # account row.
            # accountnumber = None
            try:
                int(bsb)
            except ValueError:
                # CBA credit card has 'Awards' as text within the BSB field.
                if bsb.lower() == 'awards':
                    pass
            except TypeError:
                # BSB is None. Move on.
                continue
            else:
                accountnumber = "{0}{1}".format(bsb, accountnumber)

            if accountnumber:
                # Skip CommSec accounts.
                if nickname.lower() == 'commsec shares':
                    continue

                if nickname.lower() == 'home loan':
                    home_loan = True

                filename = banalutil.filename(
                    accountnumber, self.from_date, self.to_date
                )
                accounts[accountnumber] = account(
                    nickname=nickname, balance=balance, funds=funds,
                    href=href, filename=filename, home_loan=home_loan
                )

        return accounts

    def logout(self):
        submit_button = self.driver.find_element_by_id(
            'ctl00_HeaderControl_logOffLink'
        )
        submit_button.click()

    def access_homepage(self):
        self.driver.get(self.homepage)

    def access_account(self, accountnumber):
        href = self.accounts[accountnumber].href
        self.driver.get(href)

    def view_transactions(self):
        """ Click the view transctions link within the Home Loan
        accounts page

        Non Home Loan accounts dont have this link.
        """
        attempts = 0
        while (attempts < 2):
            attempts += 1
            try:
                search_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (By.XPATH, '//*[@id="lnk-transactions-viewAll"]')
                    )
                )
            except (TimeoutException, StaleElementReferenceException):
                pass
            else:
                search_elem.click()
                break

    def download_ofx(self, filename):
        attempts = 0
        while (attempts < 2):
            attempts += 1
            try:
                export_elem = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            '//*[@id="ctl00_ToobarFooterRight_updatePanelExport"]/div/a' # noqa[E501]
                        )
                    )
                )
            except (
                NoSuchElementException,
                WebDriverException,
                TimeoutException
            ) as e:
                print(e)
                embed()
            else:
                export_elem.send_keys(Keys.NULL)
                export_elem.click()
                break

        time.sleep(2)

        try:
            export_type_elem = Select(
                self.driver.find_element_by_xpath(
                    '//*[@id="ctl00_ToobarFooterRight_ddlExportType_field"]'
                )
            )
        except (NoSuchElementException, WebDriverException) as e:
            print(e)
            embed()
        else:
            export_type_elem.select_by_value('OFX')

        try:
            submit_button = self.driver.find_element_by_xpath(
                '//*[@id="ctl00_ToobarFooterRight_lbExport"]'
            )
        except (NoSuchElementException, WebDriverException) as e:
            print(e)
            embed()
        else:
            submit_button.click()
            time.sleep(2)
            shutil.move('OFXData.ofx', filename)
