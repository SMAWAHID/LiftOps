from pydantic import BaseModel, Field

class UserBase(BaseModel):
    email: str
    full_name: str | None = None

class UserCreate(UserBase):
    password: str = Field(min_length=6)

class User(UserBase):
    id: str
    role: str  # 'admin' | 'user'
    tier: str  # 'pilot' | 'commander'
    created_at: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

class LoginRequest(BaseModel):
    username: str # email
    password: str

class SocialLoginRequest(BaseModel):
    provider: str
    email: str
    full_name: str | None = None
