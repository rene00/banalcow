from banalcow import netbank, config, penny

conf = config.Config('./config.yml')
session = netbank.Netbank(conf.netbank.username, conf.netbank.password)
session.login()

accounts = session.accounts

for account, data in accounts.items():
    session.access_account(account)
    session.set_date_widget()
    session.download_ofx(data.filename)
    session.access_homepage()

session.logout()

if conf.penny:
    session = penny.Penny(
        conf.penny.base_url, conf.penny.username, conf.penny.password
    )
    session.login()
    for account, data in accounts.items():
        session.upload(data.filename)

    session.logout()

session.driver.quit()
