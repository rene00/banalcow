from urllib.parse import urljoin
from collections import namedtuple
import os
from banalcow.driver import BanalDriver


class Penny:

    def __init__(self, base_url, username, password,
                 chrome_driver_executable_path, **kwargs):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.chrome_driver_executable_path = chrome_driver_executable_path
        self.proxy = kwargs.get('proxy')

        bd = BanalDriver(
            proxy=self.proxy,
            chrome_driver_executable_path=self.chrome_driver_executable_path
        )
        self.driver = bd.driver

    @property
    def url(self):
        _urls = namedtuple('urls', 'login transactions_import logout')
        return _urls(
            login=urljoin(self.base_url, 'login'),
            transactions_import=urljoin(self.base_url, 'transactions/import'),
            logout=urljoin(self.base_url, 'logout'),
        )

    def login(self):
        self.driver.get(self.url.login)
        user_field = self.driver.find_element_by_xpath(
            '/html/body/div/div/div/div/div[2]/form/fieldset/div[1]/input'
        )
        password_field = self.driver.find_element_by_xpath(
            '/html/body/div/div/div/div/div[2]/form/fieldset/div[2]/input'
        )
        submit_button = self.driver.find_element_by_xpath(
            '/html/body/div/div/div/div/div[2]/form/fieldset/input'
        )
        user_field.send_keys(self.username)
        password_field.send_keys(self.password)
        submit_button.click()
        self.homepage = self.driver.current_url

    def logout(self):
        self.driver.get(self.url.logout)

    def upload(self, filename):
        self.driver.get(self.url.transactions_import)
        input_field = self.driver.find_element_by_xpath('//*[@id="upload"]')
        input_field.send_keys(os.getcwd() + "/" + filename)
        submit_button = self.driver.find_element_by_xpath(
            '/html/body/div[1]/div/div[2]/div/div/div/form/div/div/input'
        )
        submit_button.click()
