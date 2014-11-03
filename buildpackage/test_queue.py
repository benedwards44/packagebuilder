from django.core.mail import send_mail

def send_test_email():
    send_mail('Hello', 'Blank email', 'ben@benedwards.co.nz', 'ben@benedwards.co.nz')