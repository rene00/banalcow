import yaml
from collections import namedtuple
import pypass


class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        with open(self.config_file, 'r') as stream:
            self.data = yaml.load(stream)
        try:
            self.pypass = pypass.PasswordStore(
                path=self.data['pypass']['path']
            )
        except TypeError:
            self.pypass = False

    @property
    def netbank(self):
        netbank = namedtuple('netbank', 'username password')
        if self.pypass:
            username = self.pypass.get_decrypted_password(
                'Personal/netbank', pypass.EntryType.username
            )
            password = self.pypass.get_decrypted_password(
                'Personal/netbank', pypass.EntryType.password
            )
        else:
            username = self.data['netbank']['username']
            password = self.data['netbank']['password']
        return netbank(
            username=str(username),
            password=str(password)
        )

    @property
    def penny(self):
        penny = namedtuple('penny', 'base_url username password')
        if self.pypass:
            base_url = yaml.load(
                self.pypass.get_decrypted_password('Personal/penny')
            )['base_url']
            username = self.pypass.get_decrypted_password(
                'Personal/penny', pypass.EntryType.username
            )
            password = self.pypass.get_decrypted_password(
                'Personal/penny', pypass.EntryType.password
            )
        else:
            base_url = self.data['penny']['base_url']
            username = self.data['penny']['username']
            password = self.data['penny']['password']
        return penny(
            base_url=str(base_url),
            username=str(username),
            password=str(password)
        )

    @property
    def chrome_driver_executable_path(self):
        try:
            return self.data['chrome_driver_executable_path']
        except KeyError:
            return None
