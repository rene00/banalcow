from banalcow import netbank, config
from IPython import embed

conf = config.Config('./config.yml')
session = netbank.Netbank(conf.netbank.username, conf.netbank.password)
session.login()
embed()
session.logout()
session.driver.quit()
