from pydantic import BaseModel, EmailStr, Field


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=120)
    password: str = Field(min_length=1, max_length=200)


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    id: str
    username: str
    email: str | None
    rol: str
    auth_type: str
    alcance_tipo: str | None = None
    alcance_id: str | None
