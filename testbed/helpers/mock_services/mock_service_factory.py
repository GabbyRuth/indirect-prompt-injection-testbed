from . import mock_service


def create_service(service_name):
    if service_name == "calendar_payload":
        mock_service.calendar_service()
    elif service_name == "email_payload" or service_name == "send_email":
        mock_service.email_service()
    elif service_name == "html_payload":
        mock_service.HTML_service()
    elif service_name == "send_money":
        mock_service.bank_service()


def load_email(email_path):
    return mock_service.load_email(email_path)
