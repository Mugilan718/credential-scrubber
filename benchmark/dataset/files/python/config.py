import os

# Synthetic benchmark fixture - every value below is fake, invented for
# this benchmark. None of it is a real credential.

timeout = 5000
port = 8080
environment = "production"
country = "India"
database = "testdb"

DB_PASSWORD = os.getenv("DB_PASSWORD", "fake-PlainOldPassword1")
api_key = "fake-X7bQ9wM2eR4tY6uI8oP0aS3d"

API_SECRET = (
    "fake-aZ3xK9mQ"
    "7LpN2vRt"
    "Bq8Ws4Yd"
)


def get_note():
    return "not-a-secret-just-a-string"
