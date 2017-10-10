from selenium import webdriver
from selenium.webdriver.common.by import By
from collections import namedtuple
import os


class Netbank:
    login_url = "https://www.my.commbank.com.au/netbank/Logon/Logon.aspx"

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.chromeOpts = webdriver.ChromeOptions()
        self.prefs = {"download.default_directory": os.getcwd()}
        self.chromeOpts.add_experimental_option("prefs", self.prefs)

    def login(self):
        self.driver = webdriver.Chrome(chrome_options=self.chromeOpts)
        self.driver.implicitly_wait(5)
        self.driver.get(self.login_url)
        user_field = self.driver.find_element_by_id('txtMyClientNumber_field')
        password_field = self.driver.find_element_by_id('txtMyPassword_field')
        submit_button = self.driver.find_element_by_id('btnLogon_field')
        user_field.send_keys(self.username)
        password_field.send_keys(self.password)
        submit_button.click()

    @property
    def accounts(self):
        """Account information in the form of a dict of tuples."""

        table = self.driver.find_element_by_xpath(
            '//*[@id="MyPortfolioGrid1_a"]'
        )

        accounts = {}
        account = namedtuple('account', 'nickname balance funds')

        for row in table.find_elements_by_xpath(".//tr"):
            bsb = None
            for td in row.find_elements(By.TAG_NAME, 'td'):
                _class = td.get_attribute('class')
                if _class == 'BSBField':
                    bsb = td.text.replace(' ', '')
                elif _class == 'AccountNumberField':
                    accountnumber = td.text.replace(' ', '')
                elif _class == 'NicknameField FirstCol':
                    nickname = td.text
                elif _class == ('AccountBalanceField CurrencyField '
                                'CurrencyFieldBold'):
                    balance = td.text
                elif _class == 'AvailableFundsField CurrencyField LastCol':
                    funds = td.text

            # If bsb can be coerced into an int, we are dealing with an
            # account row.
            try:
                int(bsb)
            except (TypeError, ValueError):
                pass
            else:
                accountnumber = "{0}{1}".format(bsb, accountnumber)
                accounts[accountnumber] = account(
                    nickname=nickname, balance=balance, funds=funds
                )

        return accounts

    def logout(self):
        submit_button = self.driver.find_element_by_id(
            'ctl00_HeaderControl_logOffLink'
        )
        submit_button.click()
