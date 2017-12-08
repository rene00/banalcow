import os
from selenium import webdriver


class BanalDriver:
    def __init__(self, **kwargs):

        self.proxy = kwargs.get('proxy')
        self.executable_path = kwargs.get(
            'executable_path', '/usr/lib/chromium-browser/chromedriver'
        )
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
            executable_path=self.executable_path,
        )
