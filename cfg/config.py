import os

from dotenv import load_dotenv
from pydantic import BaseConfig


load_dotenv()


class Settings(BaseConfig):
    # TG BOT CREDS
    TG_TOKEN: str = os.getenv("TG_TOKEN")

    # GOOGLE SHEETS TOKEN
    GGL_SHEET_TOKEN: str = os.getenv("GGL_SHEET_TOKEN")


settings = Settings()
