from .email import email_handler



def calendar_service():
    pass


def email_service():
    return email_handler.start_email_server()


def load_email(email_path):
    return email_handler.load_email_file(email_path)


def HTML_service():
    pass


def bank_service():
    pass