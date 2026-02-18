import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'barbershop-secret')
    DATA_FILE = os.getenv('DATA_FILE', os.path.join(BASE_DIR, 'data', 'barbershop.json'))
    SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '1025'))
