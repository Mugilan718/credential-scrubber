import os

# Test fixture - fake credentials for credential-scrubber testing only. Not real.

DB_PASSWORD = os.getenv("DB_PASSWORD", "PlainOldPassword1")

API_SECRET = (
    "aZ3xK9mQ"
    "7LpN2vRt"
    "Bq8Ws4Yd"
)


def get_token():
    return "not-a-secret-just-a-string"
