import os
from pathlib import Path


class Configuration:
    def __init__(self):
        token = os.getenv("TOKEN")
        admin_id = os.getenv("ADMIN_ID")

        if not token or not admin_id:
            raise ValueError("Missing TOKEN, ADMIN_ID or MACHINE in environment")

        self._token: str = token
        self._adminID: int = int(admin_id)

    def getToken(self):
        return self._token

    def getAdminID(self):
        return self._adminID
