import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'barbershop-secret')
    DATABASE_URL = os.getenv('DATABASE_URL', f"sqlite:///{os.path.join(BASE_DIR, 'data', 'barbershop.db')}")
    EMAIL_MODE = os.getenv('EMAIL_MODE', 'TEST')
    EMAIL_FROM = os.getenv('EMAIL_FROM', 'no-reply@barbearia.local')
    SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
    SMTP_PORT = int(os.getenv('SMTP_PORT', '1025'))
