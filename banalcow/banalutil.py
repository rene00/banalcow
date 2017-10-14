import datetime


def pastdt(days=365):
    """Return a dt object days in the past."""
    return (datetime.datetime.now() - datetime.timedelta(days=days))


def filename(account, from_date, to_date):
    """Return filename to be used to save OFX file."""
    return '{0}-{1}-{2}.ofx'.format(
        account, from_date.strftime('%Y%m%d'), to_date.strftime('%Y%m%d')
    )
