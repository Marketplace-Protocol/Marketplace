from os import environ

MONGODB_CONNECT_URL = environ.get("MONGODB_CONNECT_URL")
STRIPE_KEY = environ.get("STRIPE_KEY")