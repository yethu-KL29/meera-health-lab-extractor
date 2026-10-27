"""Shared Pydantic definition for Gemini generation and local validation."""
from pydantic import BaseModel, ConfigDict, Field, field_validator


class LabTest(BaseModel):
    model_config = ConfigDict(strict=True, extra='allow', allow_inf_nan=False)

    test_name: str = Field(min_length=1, description='Test name as printed on the report.')
    value: str | int | float | None = Field(
        description='Printed result; preserve qualitative text, comparators, intervals, and digit grouping.')
    unit: str | None = Field(description='Printed unit, or null when absent.')
    reference_range: str | None = Field(description='Printed range without its unit, or null when absent.')

    @field_validator('test_name')
    @classmethod
    def require_readable_name(cls, value: str) -> str:
        if not value.strip():
            raise ValueError('Test name must not be blank.')
        return value


class LabReport(BaseModel):
    model_config = ConfigDict(strict=True, extra='allow', allow_inf_nan=False)

    tests: list[LabTest] = Field(description='One result row per entry, in printed page and table order.')
