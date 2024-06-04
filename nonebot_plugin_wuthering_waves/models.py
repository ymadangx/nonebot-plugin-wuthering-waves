from __future__ import annotations

from pydantic import BaseModel


class UserInfo(BaseModel):
    enableChildMode: bool
    gender: int
    signature: str
    headUrl: str
    headCode: str
    userName: str
    userId: str
    isRegister: int
    isOfficial: int
    status: int
    unRegistering: bool
    token: str


class ResponseData(BaseModel):
    code: int
    data: UserInfo
    msg: str
    success: bool
