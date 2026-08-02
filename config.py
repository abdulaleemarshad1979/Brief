import os

USER_NAME = os.getenv("USER_NAME", "Abdul")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

LOCATIONS = [
    {"name": "Rajahmundry", "latitude": 17.0052, "longitude": 81.7778},
    {"name": "Ramachandrapuram", "latitude": 16.8364, "longitude": 82.0287},
    {"name": "Kakinada", "latitude": 16.9891, "longitude": 82.2475},
    {"name": "Aditya University, Surampalem", "latitude": 17.0818, "longitude": 82.0668},
]

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", EMAIL_ADDRESS)

MAX_WORLD = 6
MAX_INDIA = 7
MAX_AP = 4
MAX_TECH = 7
MAX_HN = 4
