import os

USER_NAME = os.getenv("USER_NAME", "Abdul")
CITY_NAME = os.getenv("CITY_NAME", "Rajahmundry")
LATITUDE = float(os.getenv("LATITUDE", "17.0005"))
LONGITUDE = float(os.getenv("LONGITUDE", "81.8040"))
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", EMAIL_ADDRESS)

MAX_WORLD = 6
MAX_INDIA = 7
MAX_AP = 4
MAX_TECH = 7
MAX_HN = 4
