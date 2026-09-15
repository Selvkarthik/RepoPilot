from pydantic import BaseModel, Field, field_validator

class AskRequest(BaseModel):
    repository: str = Field(
        ..., pattern=r"^[^/\s]+/[^/\s]+$", max_length=200
    )
    question: str = Field(..., min_length=1, max_length=2000)

    @field_validator("question")
    @classmethod
    def question_must_contain_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Question must contain text.")
        return value

class AskResponse(BaseModel):
    repository: str
    answer: str
