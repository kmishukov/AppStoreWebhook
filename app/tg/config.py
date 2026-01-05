import os

from pathlib import Path

class Configuration:
    def __init__(self):
        token = os.get("TOKEN")
        admin_id = os.get("ADMIN_ID")

        if not token or not admin_id or not machine:
            raise ValueError("Missing TOKEN, ADMIN_ID or MACHINE in environment")

        self._token: str = token
        self._adminID: int = int(admin_id)

    def getToken(self):
        return self._token

    def getAdminID(self):
        return self._adminID