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
TELUGU_RECIPIENT_EMAILS = [
    email.strip()
    for email in os.getenv("TELUGU_RECIPIENT_EMAILS", "").split(",")
    if email.strip()
]

WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_RECIPIENT_NUMBER = os.getenv("WHATSAPP_RECIPIENT_NUMBER", "")
WHATSAPP_TEMPLATE_NAME = os.getenv(
    "WHATSAPP_TEMPLATE_NAME",
    "daily_telugu_briefing",
)
WHATSAPP_TEMPLATE_LANGUAGE = os.getenv(
    "WHATSAPP_TEMPLATE_LANGUAGE",
    "te",
)
WHATSAPP_GRAPH_API_VERSION = os.getenv(
    "WHATSAPP_GRAPH_API_VERSION",
    "v23.0",
)

MAX_WORLD = 4
MAX_INDIA = 4
MAX_AP = 3
MAX_TECH = 4
MAX_RESEARCH = 3
MAX_HN = 4

OUTPUT_PATH = os.path.join("output", "briefing.html")
