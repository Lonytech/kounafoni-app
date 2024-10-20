from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, field_validator


class SummaryDuration(str, Enum):
    SHORT_DURATION: str = "1 minute"
    MEDIUM_DURATION: str = "5 minutes"
    LONG_DURATION: str = "10 minutes"


class LLMModelName(str, Enum):
    OLLAMA_OCCIGLOT: str = "mayflowergmbh/occiglot-7b-fr-en-instruct:latest"
    OLLAMA_LLAMA3: str = "llama3:8b-instruct-q2_K"
    GROQ_LLAMA3: str = "llama3-70b-8192"


class ScrapDate(BaseModel):
    end_date: date
    begin_date: date

    @field_validator("begin_date")  # type: ignore
    def validate_begin_date(cls, value: date, values: dict[str, Any]) -> date:
        end_date = values.data.get("end_date")  # type: ignore
        if value > end_date:
            raise ValueError("End date must be greater or equal than the begin date.")
        return value

    # TODO : Add field validator to check if end_date is greater than today
    # @field_validator("end_date")
    # def validate_end_date(cls, value: date):
    #     if value > date.today():
    #         raise ValueError("End date must not be greater than today.")
    #     return value
