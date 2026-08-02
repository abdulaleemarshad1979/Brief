import os

USER_NAME = os.getenv("USER_NAME", "Abdul")
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kolkata")

LOCATIONS = [
    {"name": "Rajahmundry", "latitude": 17.0052, "longitude": 81.7778},
    {"name": "Ramachandrapuram", "latitude": 16.8364, "longitude": 82.0287},
    {"name": "Kakinada", "latitude": 16.9891, "longitude": 82.2475},
    {"name": "Aditya University, Surampalem", "latitude": 17.0818, "longitude": 82.0668},
]

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
RECIPIENT_EMAIL = os.getenv("RECIPIENT_EMAIL", EMAIL_ADDRESS)

MAX_WORLD = 5
MAX_INDIA = 5
MAX_AP = 4
MAX_TECH = 5
MAX_RESEARCH = 4
MAX_HN = 4

OUTPUT_PATH = os.path.join("output", "briefing.html")
