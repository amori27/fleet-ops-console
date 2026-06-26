import enum
import uuid

from pydantic import BaseModel


class Role(enum.IntEnum):
    VIEWER = 10
    COMMANDER = 20
    ADMIN = 30

    def __str__(self) -> str:
        return self.name.lower()


class OpsUser(BaseModel):
    id: str
    username: str
    role: Role
    token: str = ""
