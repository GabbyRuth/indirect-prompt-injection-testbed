from .email import email_handler
from .calendar import calendar_handler
from .website import website_handler
from .bank import bank_handler
from .ssh import ssh_handler



def calendar_service(asset_dir=None):
    return calendar_handler.start_calendar_server(asset_dir)


def email_service():
    return email_handler.start_email_server()


def load_email(email_path):
    return email_handler.load_email_file(email_path)


def HTML_service(asset_dir=None):
    return website_handler.start_website_server(asset_dir)


def bank_service():
    return bank_handler.start_bank_server()


def ssh_service():
    return ssh_handler.start_ssh_server()