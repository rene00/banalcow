import yaml
from collections import namedtuple


class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        with open(self.config_file, 'r') as stream:
            self.data = yaml.load(stream)

    @property
    def netbank(self):
        netbank = namedtuple('netbank', 'username password')
        username = self.data['netbank']['username']
        password = self.data['netbank']['password']
        return netbank(
            username=str(username),
            password=str(password)
        )

    @property
    def penny(self):
        penny = namedtuple('penny', 'login_url username password')
        login_url = self.data['penny']['login_url']
        username = self.data['penny']['username']
        password = self.data['penny']['password']
        return penny(
            login_url=str(login_url),
            username=str(username),
            password=str(password)
        )
