from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class JobCreate(BaseModel):
    prompt: str = Field(min_length=5, description="Software feature request")


class JobOut(BaseModel):
    id: str
    status: str
    prompt: str
    result_code: str = ""
    result_tests: str = ""

    class Config:
        from_attributes = True
