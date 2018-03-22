import os
from selenium import webdriver


class BanalDriver:
    def __init__(self, chrome_driver_executable_path, **kwargs):

        self.proxy = kwargs.get('proxy')
        self.chrome_driver_executable_path = chrome_driver_executable_path

        options = webdriver.ChromeOptions()

        if self.proxy:
            options.add_argument(
                '--proxy-server=http://{0}'.format(self.proxy)
            )

        options.add_experimental_option(
            'prefs',
            {
                "download.default_directory": os.getcwd(),
                "download.prompt_for_download": False
            }
        )

        self.driver = webdriver.Chrome(
            chrome_options=options,
            executable_path=self.chrome_driver_executable_path
        )
