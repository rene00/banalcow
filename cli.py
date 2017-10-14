from banalcow import netbank, config

conf = config.Config('./config.yml')
session = netbank.Netbank(conf.netbank.username, conf.netbank.password)
session.login()

for account, data in session.accounts.items():
    session.access_account(account)
    session.set_date_widget()
    session.download_ofx(data.filename)
    session.access_homepage()

session.logout()
session.driver.quit()
