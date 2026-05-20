from datetime import date, datetime
from pydantic import BaseModel, Field, field_validator

class EmployeeCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200)
    position: str = Field(..., min_length=1, max_length=200)
    hired_at: date | None = None

    @field_validator("full_name", "position")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Field must not be blank")
        return v.strip()

class EmployeeOut(BaseModel):
    id: int
    department_id: int
    full_name: str
    position: str
    hired_at: date | None
    created_at: datetime

    model_config = {"from_attributes": True}

class DepartmentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name must not be blank")
        return v.strip()

class DepartmentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    parent_id: int | None = None

    @field_validator("name")
    @classmethod
    def not_blank(cls, v: str | None) -> str | None:
        if v is not None and not v.strip():
            raise ValueError("Name must not be blank")
        return v.strip() if v else v

class DepartmentOut(BaseModel):
    id: int
    name: str
    parent_id: int | None
    created_at: datetime

    model_config = {"from_attributes": True}

class DepartmentTree(DepartmentOut):
    employees: list[EmployeeOut] = []
    children: list["DepartmentTree"] = []